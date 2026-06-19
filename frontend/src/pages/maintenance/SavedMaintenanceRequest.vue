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
            {{ req.issue_type }} ·
            {{ locationDisplay(req) }} ·
            <span :class="priorityTextClass(req.priority)">{{ req.priority }}</span>
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="router.push('/maintenance/request')"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
            Request List
          </button>

          <!-- Edit (unapproved only) -->
          <template v-if="req.approved === 'Pending' && req.status === 'Pending'">
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
          <button v-if="req.approved === 'Pending' && req.status === 'Pending' && !editMode"
            @click="openApproveModal"
            class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
            Approve
          </button>

          <!-- Reject -->
          <button v-if="req.approved === 'Pending' && req.status === 'Pending' && !editMode"
            @click="rejectRequest"
            class="px-4 py-2 text-xs font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50">
            Reject
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
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">Location:</span>
          <span class="text-xs font-medium text-gray-700">{{ locationDisplay(req) }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">Priority:</span>
          <span class="text-xs font-semibold" :class="priorityTextClass(req.priority)">{{ req.priority }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">Approved:</span>
          <span class="text-xs font-semibold" :class="approvedClass(req.approved)">{{ req.approved }}</span>
        </div>
        <div v-if="req.approved_on" class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">Approved at:</span>
          <span class="text-xs text-gray-600">{{ formatDate(req.approved_on) }}</span>
        </div>
        <div v-if="req.technician_name" class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">Technician:</span>
          <span class="text-xs text-gray-700 font-medium">{{ req.technician_name }}</span>
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

          <!-- VIEW mode -->
          <template v-if="!editMode">

            <!-- Request Details -->
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

              <!-- Location -->
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                <div>
                  <p class="text-xs text-gray-400 mb-1">Location Type</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ req.location_type }}</div>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-1">
                    {{ req.location_type === 'Room' ? 'Room' : req.location_type === 'Asset Location' ? 'Asset Location' : 'Location' }}
                  </p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                    <template v-if="req.location_type === 'Room'">
                      {{ req.room_number || '—' }}<span v-if="req.room" class="text-gray-400 ml-1">({{ req.room }})</span>
                    </template>
                    <template v-else-if="req.location_type === 'Asset Location'">
                      {{ req.asset_location || '—' }}
                    </template>
                    <template v-else>{{ req.location || '—' }}</template>
                  </div>
                </div>
              </div>

              <!-- People -->
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                <div>
                  <p class="text-xs text-gray-400 mb-1">Reported By</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ req.reported_by_name || req.reported_by || '—' }}</div>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-1">Requesting Department</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ req.requesting_department || '—' }}</div>
                </div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                <div>
                  <p class="text-xs text-gray-400 mb-1">Supervisor / Witness</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                    {{ witnessName || req.witness_employee || '—' }}
                  </div>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-1">Witness Department</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ req.witness_department || '—' }}</div>
                </div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                <div v-if="req.asset">
                <p class="text-xs text-gray-400 mb-1">Asset</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700 font-medium">{{ req.asset }}</div>
              </div>
              <div>
                  <p class="text-xs text-gray-400 mb-1">Reported At</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ formatDate(req.reported_at) }}</div>
                </div>
                <div v-if="req.assigned_technician">
                  <p class="text-xs text-gray-400 mb-1">Assigned Technician</p>
                  <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ req.technician_name || req.assigned_technician }}</div>
                </div>
              </div>
            </div>

            <!-- Issue Description -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Issue Description</h3>
              <div v-if="req.issue_description" class="bg-gray-50 rounded-lg px-3 py-3 text-xs text-gray-700 leading-relaxed"
                v-html="req.issue_description"></div>
              <p v-else class="text-xs text-gray-400 italic">No description provided.</p>
            </div>

            <!-- Photos -->
            <div v-if="req.image_1 || req.image_2 || req.image_3" class="bg-white rounded-xl border border-gray-200 p-5">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Photos</h3>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
                <a v-for="(img, idx) in [req.image_1, req.image_2, req.image_3].filter(Boolean)" :key="idx"
                  :href="img" target="_blank" rel="noopener">
                  <img :src="img" class="w-full h-28 object-cover rounded-lg border border-gray-200 hover:opacity-90" />
                </a>
              </div>
            </div>

          </template>

          <!-- EDIT mode -->
          <template v-else>
            <div class="bg-white rounded-xl border border-blue-200 p-5">
              <div class="flex items-center gap-2 mb-4">
                <h3 class="text-sm font-bold text-gray-900">Edit Request</h3>
                <span class="px-2 py-0.5 text-[10px] font-semibold bg-blue-100 text-blue-700 rounded-full">Editing</span>
              </div>

              <!-- Location Type -->
              <div class="mb-4">
                <p class="text-xs text-gray-500 mb-1.5">Location Type <span class="text-red-400">*</span></p>
                <div class="flex rounded-lg overflow-hidden border border-gray-200 h-[38px]">
                  <button @click="editForm.location_type = 'Room'"
                    class="flex-1 text-xs font-medium transition-colors"
                    :class="editForm.location_type === 'Room' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'">
                    🏨 Room
                  </button>
                  <button @click="editForm.location_type = 'Asset Location'"
                    class="flex-1 text-xs font-medium transition-colors border-l border-gray-200"
                    :class="editForm.location_type === 'Asset Location' ? 'bg-purple-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'">
                    🔧 Asset Location
                  </button>
                  <button @click="editForm.location_type = 'Other Location'"
                    class="flex-1 text-xs font-medium transition-colors border-l border-gray-200"
                    :class="editForm.location_type === 'Other Location' ? 'bg-orange-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'">
                    📍 Other
                  </button>
                </div>
              </div>

              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                <div v-if="editForm.location_type === 'Room'">
                  <p class="text-xs text-gray-500 mb-1.5">Room <span class="text-red-400">*</span></p>
                  <select v-model="editForm.room"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                    <option value="">— select room —</option>
                    <option v-for="r in rooms" :key="r.name" :value="r.name">{{ r.room_number || r.name }}</option>
                  </select>
                </div>
                <div v-else-if="editForm.location_type === 'Asset Location'">
                  <p class="text-xs text-gray-500 mb-1.5">Asset Location <span class="text-red-400">*</span></p>
                  <input v-model="editForm.asset_location" type="text" placeholder="e.g. Generator Room, Pump Room..."
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-300" />
                </div>
                <div v-else>
                  <p class="text-xs text-gray-500 mb-1.5">Location <span class="text-red-400">*</span></p>
                  <input v-model="editForm.location" type="text" placeholder="e.g. Laundry, Gym..."
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Issue Type <span class="text-red-400">*</span></p>
                  <select v-model="editForm.issue_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                    <option value="Plumbing">Plumbing</option><option value="Electrical">Electrical</option>
                    <option value="HVAC">HVAC</option><option value="Furniture">Furniture</option>
                    <option value="Appliance">Appliance</option><option value="Electronics">Electronics</option>
                    <option value="Structural">Structural</option><option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Priority <span class="text-red-400">*</span></p>
                  <select v-model="editForm.priority" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                    <option value="Low">Low</option><option value="Medium">Medium</option>
                    <option value="High">High</option><option value="Critical">Critical</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Reported By <span class="text-red-400">*</span></p>
                  <select v-model="editForm.reported_by" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                    <option value="">— select employee —</option>
                    <option v-for="e in employees" :key="e.name" :value="e.name">
                      {{ e.employee_name }}{{ e.department ? ` · ${e.department}` : '' }}
                    </option>
                  </select>
                </div>
              </div>

              <div class="mb-4">
                <p class="text-xs text-gray-500 mb-1.5">Reported At <span class="text-red-400">*</span></p>
                <input v-model="editForm.reported_at" type="datetime-local"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
              </div>


              <div class="mb-4">
                <p class="text-xs text-gray-500 mb-1.5">Asset <span class="text-gray-400">(optional)</span></p>
                <select v-model="editForm.asset"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                  <option value="">— no specific asset —</option>
                  <option v-for="a in assets" :key="a.name" :value="a.name">
                    {{ a.asset_name || a.name }}{{ a.asset_category ? ` · ${a.asset_category}` : '' }}
                  </option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Issue Description</p>
                <textarea v-model="editForm.issue_description" rows="4" placeholder="Describe the issue..."
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Photos <span class="text-gray-400">(optional, up to 3)</span></p>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
                  <div v-for="idx in [0, 1, 2]" :key="idx">
                    <p class="text-[10px] text-gray-400 mb-1">{{ idx === 0 ? 'Image 1 (Primary)' : `Image ${idx + 1}` }}</p>
                    <!-- newly selected replacement preview -->
                    <div v-if="editImagePreviews[idx]" class="relative">
                      <img :src="editImagePreviews[idx]" class="w-full h-24 object-cover rounded-lg border border-gray-200" />
                      <button type="button" @click="removeEditImage(idx)"
                        class="absolute top-1 right-1 bg-white/90 rounded-full w-5 h-5 flex items-center justify-center text-xs text-gray-600 hover:text-red-600 shadow">✕</button>
                    </div>
                    <!-- existing saved image -->
                    <div v-else-if="editImageUrls[idx]" class="relative">
                      <img :src="editImageUrls[idx]" class="w-full h-24 object-cover rounded-lg border border-gray-200" />
                      <button type="button" @click="removeEditImage(idx)"
                        class="absolute top-1 right-1 bg-white/90 rounded-full w-5 h-5 flex items-center justify-center text-xs text-gray-600 hover:text-red-600 shadow">✕</button>
                    </div>
                    <!-- empty slot -->
                    <label v-else
                      class="flex flex-col items-center justify-center h-24 border border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 text-gray-400">
                      <span class="text-lg leading-none">📷</span>
                      <span class="text-[10px] mt-1">Add photo</span>
                      <input type="file" accept="image/*" class="hidden" @change="onEditImageChange(idx, $event)" />
                    </label>
                  </div>
                </div>
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
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ req.task_technician_name || req.technician_name || '—' }}</div>
              </div>
            </div>
          </div>

          

          <div v-if="req.status === 'Completed'" class="bg-green-50 rounded-xl border border-green-200 p-4 text-center">
            <span class="text-xs text-green-600 font-semibold">✓ Request Completed</span>
            <p v-if="req.completion_date" class="text-xs text-green-500 mt-1">{{ formatDate(req.completion_date) }}</p>
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
                <span class="text-xs font-semibold" :class="statusTextClass(req.status)">{{ req.status }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Location Type</span>
                <span class="text-xs font-medium text-gray-700">
                  {{ req.location_type === 'Room' ? '🏨 Room' : req.location_type === 'Asset Location' ? '🔧 Asset' : '📍 Other' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Issue Type</span>
                <span class="text-xs font-medium text-gray-700">{{ req.issue_type }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Location</span>
                <span class="text-xs font-medium text-gray-700 text-right max-w-[140px] truncate">{{ locationDisplay(req) }}</span>
              </div>
              <div class="flex justify-between pt-1 border-t border-gray-100">
                <span class="text-xs text-gray-400">Reported By</span>
                <span class="text-xs text-gray-600 text-right max-w-[140px] truncate">{{ req.reported_by_name || req.reported_by || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Dept</span>
                <span class="text-xs text-gray-600 text-right max-w-[140px] truncate">{{ req.requesting_department || '—' }}</span>
              </div>
              <div class="flex justify-between pt-1 border-t border-gray-100">
                <span class="text-xs text-gray-400">Witness</span>
                <span class="text-xs text-gray-600 text-right max-w-[140px] truncate">{{ witnessName || req.witness_employee || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-400">Witness Dept</span>
                <span class="text-xs text-gray-600 text-right max-w-[140px] truncate">{{ req.witness_department || '—' }}</span>
              </div>
              <div class="flex justify-between pt-1 border-t border-gray-100">
                <span class="text-xs text-gray-400">Approved</span>
                <span class="text-xs font-semibold" :class="approvedClass(req.approved)">{{ req.approved }}</span>
              </div>
              <div v-if="req.approved_by" class="flex justify-between">
                <span class="text-xs text-gray-400">Approved By</span>
                <span class="text-xs text-gray-600">{{ req.approved_by }}</span>
              </div>
              <div v-if="req.technician_name" class="flex justify-between">
                <span class="text-xs text-gray-400">Technician</span>
                <span class="text-xs font-medium text-gray-700">{{ req.technician_name }}</span>
              </div>
              <div v-if="req.asset" class="flex justify-between">
                <span class="text-xs text-gray-400">Asset</span>
                <span class="text-xs font-medium text-gray-700 truncate max-w-[130px]">{{ req.asset }}</span>
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

            <button v-if="req.approved === 'Pending' && req.status === 'Pending' && !editMode"
              @click="openApproveModal"
              class="w-full py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700">
              ✓ Approve Request
            </button>

            <button v-if="req.approved === 'Pending' && req.status === 'Pending' && !editMode"
              @click="rejectRequest"
              class="w-full py-2.5 text-xs font-medium text-red-600 border border-red-200 rounded-xl hover:bg-red-50">
              ✕ Reject Request
            </button>

            <button v-if="req.linked_task"
              @click="router.push({ name: 'MaintenanceTask', params: { id: req.linked_task.name } })"
              class="w-full py-2.5 text-xs font-semibold text-blue-600 border border-blue-200 rounded-xl hover:bg-blue-50">
              Open Linked Task
            </button>

            <div v-if="req.approved === 'Approved'" class="px-3 py-2.5 bg-green-50 rounded-lg border border-green-100 flex items-center gap-2">
              <span class="text-green-500">✓</span>
              <span class="text-xs text-green-700">Approved {{ formatDate(req.approved_on) }}</span>
            </div>

            <div v-if="req.approved === 'Rejected'" class="px-3 py-2.5 bg-red-50 rounded-lg border border-red-100 flex items-center gap-2">
              <span class="text-red-500">✕</span>
              <span class="text-xs text-red-700">Rejected</span>
            </div>

            <!-- Workflow hint -->
            <div class="px-3 py-2.5 bg-gray-50 rounded-lg border border-gray-100 mt-2">
              <p class="text-xs text-gray-500 font-medium mb-1">Workflow</p>
              <p class="text-xs text-gray-400">1. Assign technician &amp; witness, approve</p>
              <p class="text-xs text-gray-400 mt-0.5">2. Maintenance Task auto-created</p>
              <p class="text-xs text-gray-400 mt-0.5">3. Technician completes work</p>
              <p class="text-xs text-gray-400 mt-0.5">4. Witness verifies → Manager approves</p>
              <p class="text-xs text-gray-400 mt-0.5">5. Request marked Completed</p>
            </div>
          </div>

        </div>
      </div>

    </template>

    <!-- Approve Modal -->
    <Teleport to="body">
      <div v-if="showApproveModal" class="fixed inset-0 z-50 flex items-center justify-center"
        style="background:rgba(0,0,0,0.55);" @click.self="showApproveModal = false">
        <div class="bg-white rounded-2xl shadow-2xl w-full mx-4 overflow-y-auto" style="max-width:480px;max-height:90vh;">
          <div class="p-6">
            <div class="flex items-start justify-between mb-5">
              <div>
                <h2 class="text-base font-bold text-gray-900">Approve Request</h2>
                <p class="text-xs text-gray-400 mt-1">Assign a technician and supervisor/witness, then approve. A Maintenance Task will be created automatically.</p>
              </div>
              <button @click="showApproveModal = false" class="text-gray-400 hover:text-gray-600 text-lg">✕</button>
            </div>

            <div class="mb-4">
              <p class="text-xs text-gray-500 mb-1.5">Assign Technician <span class="text-red-400">*</span></p>
              <select v-model="approveForm.assigned_technician"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                <option value="">— select technician —</option>
                <option v-for="t in availableTechnicians" :key="t.name" :value="t.name">
                  {{ t.technician_name }}{{ t.availability !== 'Available' ? ` (${t.availability})` : '' }}
                </option>
              </select>
              <p v-if="approveForm.witness_employee && availableTechnicians.length < technicians.length" class="text-xs text-gray-400 mt-1">
                The selected witness is hidden from this list — a technician can't also be the supervisor.
              </p>
            </div>

            <div class="mb-5">
              <p class="text-xs text-gray-500 mb-1.5">Supervisor / Witness <span class="text-red-400">*</span></p>
              <select v-model="approveForm.witness_employee"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                <option value="">— select supervisor / witness —</option>
                <option v-for="e in employees" :key="e.name" :value="e.name">
                  {{ e.employee_name }}{{ e.department ? ` · ${e.department}` : '' }}
                </option>
              </select>
              <p v-if="approveForm.witness_employee" class="text-xs text-green-600 mt-1">
                ✓ Pre-filled from request — change if needed
              </p>
              <p v-else class="text-xs text-gray-400 mt-1">This person will verify the completed work before the Manager approves.</p>
            </div>

            <div class="flex items-center justify-end gap-2">
              <button @click="showApproveModal = false" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
              <button @click="approveRequest" :disabled="approving"
                class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
                <svg v-if="approving" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                {{ approving ? 'Approving...' : 'Approve' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'
import { callMethodForm, requestApi } from '@/lib/api'

const router = useRouter()
const route = useRoute()
const requestId = route.params.id

const loading = ref(true)
const loadError = ref(null)
const approving = ref(false)
const saving = ref(false)
const showApproveModal = ref(false)
const editMode = ref(false)
const req = ref(null)
const technicians = ref([])
const rooms = ref([])
const employees = ref([])
const assets = ref([])

const editForm = ref({})
const approveForm = ref({ assigned_technician: '', witness_employee: '' })

// Exclude any technician whose linked Employee is the currently selected witness —
// that pairing is rejected on approval (technician can't also be the supervisor),
// so hide it up front rather than letting the user pick it and hit an error.
const availableTechnicians = computed(() => {
  const witness = approveForm.value.witness_employee
  if (!witness) return technicians.value
  return technicians.value.filter(t => t.employee !== witness)
})

// If the witness changes and the currently selected technician is no longer valid, clear it.
watch(() => approveForm.value.witness_employee, () => {
  const stillValid = availableTechnicians.value.some(t => t.name === approveForm.value.assigned_technician)
  if (approveForm.value.assigned_technician && !stillValid) {
    approveForm.value.assigned_technician = ''
  }
})

// Resolve witness name from employees list
const witnessName = computed(() => {
  if (!req.value?.witness_employee) return null
  return employees.value.find(e => e.name === req.value.witness_employee)?.employee_name || null
})

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
const reqResource      = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_maintenance_request', auto: false })
const approveResource  = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.approve_request', auto: false })
const rejectResource   = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.reject_request', auto: false })
const updateResource   = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.update_maintenance_request', auto: false })
const techResource     = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_technicians_for_request', auto: false })
const roomsResource    = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_rooms_for_request', auto: false })
const employeesResource  = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_employees_for_request', auto: false })
const assetsResource     = createResource({ url: 'rhohotel.rhocom_hotel.api.maintenance_request.get_assets_for_request', auto: false })

// ─── Load ─────────────────────────────────────────────────────────────────────
async function loadRequest() {
  loading.value = true
  loadError.value = null
  try {
    req.value = await reqResource.fetch({ request_name: requestId })
  } catch (e) {
    loadError.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}


// ─── Approve ──────────────────────────────────────────────────────────────────
function openApproveModal() {
  // Pre-fill witness from the existing request so user doesn't have to re-select
  approveForm.value = {
    assigned_technician: req.value.assigned_technician || '',
    witness_employee:    req.value.witness_employee    || '',
  }
  showApproveModal.value = true
}

async function approveRequest() {
  if (!approveForm.value.assigned_technician) {
    showToast('Please select a technician', 'warning'); return
  }
  if (!approveForm.value.witness_employee) {
    showToast('Please select a Supervisor / Witness', 'warning'); return
  }
  approving.value = true
  try {
    const res = await approveResource.fetch({
      request_name: requestId,
      assigned_technician: approveForm.value.assigned_technician,
      witness_employee: approveForm.value.witness_employee,
    })
    if (res?.success) {
      showToast('Request approved', 'success')
      showApproveModal.value = false
      await loadRequest()
    } else showToast('Failed: ' + (res?.error || 'Unknown'))
  } catch (e) { showToast('Error: ' + (e?.message || String(e))) }
  finally { approving.value = false }
}

// ─── Reject ───────────────────────────────────────────────────────────────────
async function rejectRequest() {
  if (!confirm('Are you sure you want to reject this request?')) return
  try {
    const res = await rejectResource.fetch({ request_name: requestId })
    if (res?.success) { showToast('Request rejected', 'warning'); await loadRequest() }
    else showToast('Failed: ' + (res?.error || 'Unknown'))
  } catch (e) { showToast('Error: ' + (e?.message || String(e))) }
}

// ─── Edit mode ────────────────────────────────────────────────────────────────
const editImageUrls = ref([null, null, null])      // existing saved image URLs, null if removed/empty
const editImageFiles = ref([null, null, null])      // newly selected files pending upload
const editImagePreviews = ref([null, null, null])   // local object URLs for newly selected files

function enterEdit() {
  editForm.value = {
    location_type:     req.value.location_type || 'Room',
    room:              req.value.room || '',
    asset_location:    req.value.asset_location || '',
    location:          req.value.location || '',
    issue_type:        req.value.issue_type || '',
    priority:          req.value.priority || 'Medium',
    reported_by:       req.value.reported_by || '',
    reported_at:       req.value.reported_at ? req.value.reported_at.slice(0, 16) : '',
    issue_description: req.value.issue_description || '',
    asset:             req.value.asset || '',
  }
  editImageUrls.value = [req.value.image_1 || null, req.value.image_2 || null, req.value.image_3 || null]
  editImageFiles.value = [null, null, null]
  editImagePreviews.value = [null, null, null]
  editMode.value = true
}

function onEditImageChange(slotIndex, event) {
  const [file] = event.target.files || []
  editImageFiles.value[slotIndex] = file || null
  if (editImagePreviews.value[slotIndex]) {
    URL.revokeObjectURL(editImagePreviews.value[slotIndex])
  }
  editImagePreviews.value[slotIndex] = file ? URL.createObjectURL(file) : null
}

function removeEditImage(slotIndex) {
  // Clears both an existing saved image and any newly-selected replacement for this slot.
  // The actual deletion on the server happens in saveEdit() via set_value(fieldname, '').
  if (editImagePreviews.value[slotIndex]) {
    URL.revokeObjectURL(editImagePreviews.value[slotIndex])
  }
  editImageUrls.value[slotIndex] = null
  editImageFiles.value[slotIndex] = null
  editImagePreviews.value[slotIndex] = null
}

function cancelEdit() { editMode.value = false; editForm.value = {} }

async function saveEdit() {
  if (editForm.value.location_type === 'Room' && !editForm.value.room) {
    showToast('Room is required', 'warning'); return
  }
  if (editForm.value.location_type === 'Asset Location' && !editForm.value.asset_location) {
    showToast('Asset Location is required', 'warning'); return
  }
  if (editForm.value.location_type === 'Other Location' && !editForm.value.location) {
    showToast('Location is required', 'warning'); return
  }
  if (!editForm.value.issue_type || !editForm.value.priority || !editForm.value.reported_by) {
    showToast('Issue Type, Priority and Reported By are required', 'warning'); return
  }
  saving.value = true
  try {
    const res = await updateResource.fetch({ request_name: requestId, request_data: editForm.value })
    if (res?.success) {
      await syncEditImages()
      showToast('Request updated', 'success'); editMode.value = false; await loadRequest()
    }
    else showToast('Failed: ' + (res?.error || 'Unknown'))
  } catch (e) { showToast('Error: ' + (e?.message || String(e))) }
  finally { saving.value = false }
}

async function syncEditImages() {
  const originalImages = [req.value.image_1 || null, req.value.image_2 || null, req.value.image_3 || null]

  for (let i = 0; i < 3; i++) {
    const fieldname = `image_${i + 1}`
    const newFile = editImageFiles.value[i]
    const wasRemoved = !editImageUrls.value[i] && !newFile && originalImages[i]

    if (newFile) {
      const body = new FormData()
      body.append('file', newFile)
      body.append('doctype', 'Maintenance Request')
      body.append('docname', requestId)
      body.append('fieldname', fieldname)
      body.append('is_private', '0')
      try {
        const payload = await requestApi('/api/method/upload_file', { method: 'POST', body })
        const fileUrl = payload?.message?.file_url || ''
        if (fileUrl) {
          await callMethodForm('frappe.client.set_value', {
            doctype: 'Maintenance Request', name: requestId, fieldname, value: fileUrl,
          })
        }
      } catch (e) {
        showToast(`Image ${i + 1} failed to upload: ` + (e?.message || String(e)), 'warning')
      }
    } else if (wasRemoved) {
      try {
        await callMethodForm('frappe.client.set_value', {
          doctype: 'Maintenance Request', name: requestId, fieldname, value: '',
        })
      } catch (e) {
        showToast(`Failed to remove image ${i + 1}: ` + (e?.message || String(e)), 'warning')
      }
    }
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function locationDisplay(r) {
  if (!r) return '—'
  if (r.location_type === 'Room') return '🏨 ' + (r.room_number || r.room || '—')
  if (r.location_type === 'Asset Location') return '🔧 ' + (r.asset_location || '—')
  return '📍 ' + (r.location || '—')
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function priorityTextClass(p) {
  return { Critical: 'text-red-600', High: 'text-orange-500', Medium: 'text-yellow-600', Low: 'text-blue-500' }[p] || 'text-gray-600'
}

function statusBadgeClass(s) {
  return {
    Pending: 'bg-blue-100 text-blue-600', Approved: 'bg-green-100 text-green-600',
    'In Progress': 'bg-purple-100 text-purple-600', Completed: 'bg-green-100 text-green-600',
    Rejected: 'bg-red-100 text-red-500', Cancelled: 'bg-red-100 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
}

function statusTextClass(s) {
  return {
    Pending: 'text-blue-600', Approved: 'text-green-600', 'In Progress': 'text-purple-600',
    Completed: 'text-green-600', Rejected: 'text-red-500', Cancelled: 'text-red-500',
  }[s] || 'text-gray-600'
}

function approvedClass(a) {
  return { Approved: 'text-green-600', Rejected: 'text-red-500', Pending: 'text-gray-400' }[a] || 'text-gray-400'
}

// ─── Init ─────────────────────────────────────────────────────────────────────
onMounted(async () => {
  await loadRequest()
  const [tRes, rRes, eRes, aRes] = await Promise.all([techResource.fetch(), roomsResource.fetch(), employeesResource.fetch(), assetsResource.fetch()])
  technicians.value = tRes || []
  rooms.value = rRes || []
  employees.value = eRes || []
  assets.value = aRes || []
})
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>