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
      <p class="text-sm text-gray-400">Loading technician profile...</p>
    </div>

    <!-- Error -->
    <div v-else-if="loadError" class="flex flex-col items-center justify-center h-64 gap-3">
      <p class="text-sm font-medium text-gray-700">Failed to load technician</p>
      <p class="text-xs text-gray-400">{{ loadError }}</p>
      <button @click="loadTechnician" class="px-4 py-2 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">Retry</button>
    </div>

    <template v-else-if="tech">

      <!-- Header -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h2 class="text-sm font-bold text-gray-900">{{ tech.technician_name }}</h2>
          <p class="text-xs text-gray-400 mt-0.5">
            {{ tech.name }} •
            {{ tech.technician_type }} •
            <span :class="availabilityTextClass(tech.availability)">{{ tech.availability }}</span>
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="router.push('/maintenance/technicians')"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
            Technician List
          </button>
          <button @click="showAssignModal = true"
            class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">
            Assign Task
          </button>
          <button v-if="!editMode" @click="enterEditMode"
            class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">
            Edit Profile
          </button>
          <template v-else>
            <button @click="cancelEdit"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
              Cancel
            </button>
            <button @click="saveEdit" :disabled="saving"
              class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center gap-1.5">
              <svg v-if="saving" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              {{ saving ? 'Saving...' : 'Save Changes' }}
            </button>
          </template>
        </div>
      </div>

      <!-- Stats -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">Technician Type</p>
            <span class="px-2.5 py-0.5 text-xs font-medium rounded-full"
              :class="tech.technician_type === 'In-House' ? 'bg-blue-100 text-blue-600' : 'bg-orange-100 text-orange-600'">
              {{ tech.technician_type === 'In-House' ? 'Employee' : 'Vendor' }}
            </span>
          </div>
          <p class="text-xl font-bold text-gray-900">{{ tech.technician_type }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">Specialization</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Primary</span>
          </div>
          <p class="text-sm font-bold text-gray-900 leading-tight">{{ tech.primary_specialization || 'Not set' }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">Availability</p>
            <span class="px-2.5 py-0.5 text-xs font-medium rounded-full"
              :class="availabilityBadgeClass(tech.availability)">
              {{ tech.availability === 'Available' ? 'Ready' : tech.availability }}
            </span>
          </div>
          <p class="text-2xl font-bold text-gray-900">{{ tech.availability }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">Open Assignments</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Live</span>
          </div>
          <p class="text-2xl font-bold text-gray-900">{{ tech.open_tasks_count }}</p>
        </div>
      </div>

      <!-- Body -->
      <div style="display:grid;grid-template-columns:1fr 320px;gap:20px;">

        <!-- Left: Details (view or edit) -->
        <div class="space-y-4">

          <!-- View Mode -->
          <div v-if="!editMode" class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Technician Details</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div>
                <p class="text-xs text-gray-400 mb-1">Technician ID</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700 font-mono">{{ tech.name }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Full Name / Company</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold text-gray-900">{{ tech.technician_name }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Technician Type</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ tech.technician_type }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">{{ tech.technician_type === 'In-House' ? 'Linked Employee' : 'Linked Supplier' }}</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
                  {{ tech.linked_name || (tech.employee || tech.supplier || '—') }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Primary Specialization</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ tech.primary_specialization || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Secondary Skills</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ tech.secondary_skills || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Phone</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ tech.phone || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Email</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ tech.email || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Availability</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold" :class="availabilityTextClass(tech.availability)">
                  {{ tech.availability }}
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Shift / Schedule</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ tech.shift || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Priority Group</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ tech.response_priority_group }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Certification</p>
                <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">{{ tech.certification || '—' }}</div>
              </div>
            </div>
            <div class="mt-4" v-if="tech.notes">
              <p class="text-xs text-gray-400 mb-1">Notes</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-600" v-html="tech.notes"></div>
            </div>
            <div class="mt-4 flex items-center gap-4">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full" :class="tech.can_receive_urgent ? 'bg-green-500' : 'bg-gray-300'"></span>
                <span class="text-xs text-gray-500">{{ tech.can_receive_urgent ? 'Receives urgent tasks' : 'No urgent tasks' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full" :class="tech.visible_for_assignment ? 'bg-green-500' : 'bg-gray-300'"></span>
                <span class="text-xs text-gray-500">{{ tech.visible_for_assignment ? 'Visible for assignment' : 'Hidden from assignment' }}</span>
              </div>
            </div>
          </div>

          <!-- Edit Mode -->
          <div v-else class="bg-white rounded-xl border border-blue-200 p-5">
            <div class="flex items-center gap-2 mb-4">
              <h3 class="text-sm font-bold text-gray-900">Edit Profile</h3>
              <span class="px-2 py-0.5 text-[10px] font-semibold bg-blue-100 text-blue-700 rounded-full">Editing</span>
            </div>

            <!-- Type toggle -->
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Full Name <span class="text-red-400">*</span></p>
                <input v-model="editForm.technician_name" type="text"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Technician Type</p>
                <div class="flex rounded-lg overflow-hidden border border-gray-200 h-[38px]">
                  <button @click="editForm.technician_type = 'In-House'"
                    class="flex-1 text-xs font-medium transition-colors"
                    :class="editForm.technician_type === 'In-House' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'">
                    In-House
                  </button>
                  <button @click="editForm.technician_type = 'Outsourced'"
                    class="flex-1 text-xs font-medium transition-colors border-l border-gray-200"
                    :class="editForm.technician_type === 'Outsourced' ? 'bg-orange-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'">
                    Outsourced
                  </button>
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Availability</p>
                <select v-model="editForm.availability"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                  <option value="Available">Available</option>
                  <option value="On Call">On Call</option>
                  <option value="Unavailable">Unavailable</option>
                </select>
              </div>
            </div>

            <!-- Linkage -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
              <div v-if="editForm.technician_type === 'In-House'">
                <p class="text-xs text-gray-500 mb-1.5">Link Employee</p>
                <select v-model="editForm.employee" @change="onEditEmployeeSelect"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                  <option value="">— select employee —</option>
                  <option v-for="emp in employees" :key="emp.name" :value="emp.name">
                    {{ emp.employee_name }}{{ emp.designation ? ` · ${emp.designation}` : '' }}
                  </option>
                </select>
              </div>
              <div v-else>
                <p class="text-xs text-gray-500 mb-1.5">Link Supplier</p>
                <select v-model="editForm.supplier" @change="onEditSupplierSelect"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                  <option value="">— select supplier —</option>
                  <option v-for="sup in suppliers" :key="sup.name" :value="sup.name">
                    {{ sup.supplier_name }}
                  </option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Primary Specialization</p>
                <select v-model="editForm.primary_specialization"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                  <option value="">Select specialization</option>
                  <option value="Laundry / Mechanical">Laundry / Mechanical</option>
                  <option value="Boiler / Heating">Boiler / Heating</option>
                  <option value="Electrical / Electronics">Electrical / Electronics</option>
                  <option value="HVAC">HVAC</option>
                  <option value="Plumbing / Pump">Plumbing / Pump</option>
                  <option value="TV / Smart Lock / IT">TV / Smart Lock / IT</option>
                  <option value="General Maintenance">General Maintenance</option>
                </select>
              </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Secondary Skills</p>
                <input v-model="editForm.secondary_skills" type="text" placeholder="e.g. Electrical, HVAC..."
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Response Priority Group</p>
                <select v-model="editForm.response_priority_group"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                  <option value="Standard">Standard</option>
                  <option value="Priority">Priority</option>
                  <option value="Emergency">Emergency</option>
                </select>
              </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Phone</p>
                <input v-model="editForm.phone" type="text"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Email</p>
                <input v-model="editForm.email" type="email"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
              </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Shift / Working Window</p>
                <input v-model="editForm.shift" type="text" placeholder="e.g. 08:00 AM – 05:00 PM"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Certification / License</p>
                <input v-model="editForm.certification" type="text"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
              </div>
            </div>

            <div class="mb-4">
              <p class="text-xs text-gray-500 mb-1.5">Notes</p>
              <textarea v-model="editForm.notes" rows="3"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
            </div>

            <div class="mb-4">
              <p class="text-xs text-gray-500 mb-1.5">Supported Asset Categories</p>
              <textarea v-model="editForm.supported_categories" rows="2"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
            </div>

            <div class="flex items-center gap-6">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="editForm.can_receive_urgent" class="w-4 h-4 accent-green-500" />
                <span class="text-xs text-gray-700">Can receive urgent tasks</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="editForm.visible_for_assignment" class="w-4 h-4 accent-green-500" />
                <span class="text-xs text-gray-700">Visible for assignment</span>
              </label>
            </div>
          </div>

          <!-- Open Assignments -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">
              Open Assignments
              <span class="ml-2 px-2 py-0.5 text-xs font-semibold bg-blue-100 text-blue-700 rounded-full">{{ tech.open_tasks_count }}</span>
            </h3>
            <div v-if="tech.open_tasks.length" class="space-y-2">
              <div v-for="task in tech.open_tasks" :key="task.name"
                class="flex items-center justify-between px-3 py-2.5 bg-gray-50 rounded-lg border border-gray-100">
                <div>
                  <p class="text-xs font-semibold text-gray-900">{{ task.name }}</p>
                  <p class="text-xs text-gray-400 mt-0.5">{{ task.task_description || task.asset || '—' }}</p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="px-2 py-0.5 text-[10px] font-semibold rounded-full"
                    :class="taskStatusClass(task.status)">{{ task.status }}</span>
                  <span class="px-2 py-0.5 text-[10px] font-semibold rounded-full"
                    :class="priorityClass(task.priority)">{{ task.priority }}</span>
                </div>
              </div>
            </div>
            <p v-else class="text-xs text-gray-400 text-center py-4">No open assignments</p>
          </div>
        </div>

        <!-- Right Column -->
        <div class="space-y-4">

          <!-- Performance -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Performance</h3>
            <div class="mb-3">
              <p class="text-xs text-gray-400 mb-1.5">Completion Score</p>
              <div class="bg-blue-50 rounded-lg px-3 py-2.5 flex items-center justify-between">
                <span class="text-xs font-semibold text-blue-700">{{ tech.completion_score }}%</span>
                <span class="text-xs text-blue-500">{{ tech.total_completed }} / {{ tech.total_tasks_assigned }} tasks</span>
              </div>
              <!-- Progress bar -->
              <div class="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full bg-blue-500 rounded-full transition-all duration-500"
                  :style="`width:${tech.completion_score}%`"></div>
              </div>
            </div>
            <div class="mb-3">
              <p class="text-xs text-gray-400 mb-1.5">Total Assigned</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700 font-semibold">{{ tech.total_tasks_assigned }} tasks</div>
            </div>
            <div>
              <p class="text-xs text-gray-400 mb-1.5">Total Completed</p>
              <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700 font-semibold">{{ tech.total_tasks_completed }} tasks</div>
            </div>
          </div>

          <!-- Recent Completed -->
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-3">Recently Completed</h3>
            <div v-if="tech.recent_completed.length" class="space-y-3">
              <div v-for="task in tech.recent_completed" :key="task.name" class="bg-gray-50 rounded-lg p-3">
                <p class="text-xs font-semibold text-gray-900">{{ formatDate(task.end_time) }}</p>
                <p class="text-xs text-gray-500 mt-0.5">{{ task.task_description || task.name }}</p>
                <p class="text-[10px] text-gray-400 mt-0.5">{{ task.asset || '' }}</p>
              </div>
            </div>
            <p v-else class="text-xs text-gray-400 text-center py-4">No completed tasks yet</p>
          </div>

          <!-- Quick Actions -->
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <p class="text-xs font-semibold text-gray-700 mb-3">Quick Actions</p>
            <div class="space-y-2">
              <button @click="setAvailability('Unavailable')" :disabled="updatingAvailability || tech.availability === 'Unavailable'"
                class="w-full py-2.5 text-xs font-semibold text-red-500 border border-red-200 rounded-xl hover:bg-red-50 disabled:opacity-40 transition-colors">
                Mark Unavailable
              </button>
              <button @click="setAvailability('On Call')" :disabled="updatingAvailability || tech.availability === 'On Call'"
                class="w-full py-2.5 text-xs font-semibold text-yellow-600 border border-yellow-200 rounded-xl hover:bg-yellow-50 disabled:opacity-40 transition-colors">
                Mark On Call
              </button>
              <button @click="setAvailability('Available')" :disabled="updatingAvailability || tech.availability === 'Available'"
                class="w-full py-2.5 text-xs font-semibold text-white bg-green-500 rounded-xl hover:bg-green-600 disabled:opacity-40 transition-colors">
                <span v-if="updatingAvailability" class="flex items-center justify-center gap-1.5">
                  <svg class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                  </svg>Updating...
                </span>
                <span v-else>Mark Available</span>
              </button>
            </div>
          </div>

        </div>
      </div>

      <!-- Assign Task Modal -->
      <Teleport to="body">
        <div v-if="showAssignModal" class="fixed inset-0 z-50 flex items-center justify-center"
          style="background:rgba(0,0,0,0.55);" @click.self="showAssignModal = false">
          <div class="bg-white rounded-2xl shadow-2xl w-full mx-4 overflow-y-auto" style="max-width:700px;max-height:90vh;">
            <div class="p-6">
              <div class="flex items-start justify-between mb-5">
                <div>
                  <h2 class="text-lg font-bold text-gray-900">Assign Task</h2>
                  <p class="text-xs text-gray-400 mt-1">Assign a maintenance work order to {{ tech.technician_name }}.</p>
                </div>
                <div class="flex items-center gap-2">
                  <button @click="showAssignModal = false" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Close</button>
                  <button @click="assignTask" :disabled="assigning || !assignForm.task"
                    class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center gap-1.5">
                    <svg v-if="assigning" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                    {{ assigning ? 'Assigning...' : 'Assign' }}
                  </button>
                </div>
              </div>

              <!-- Technician summary row -->
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-5">
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Technician</p>
                  <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold text-gray-900">{{ tech.technician_name }}</div>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Type</p>
                  <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">{{ tech.technician_type }}</div>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Availability</p>
                  <div class="px-3 py-2.5 border rounded-lg text-xs font-semibold"
                    :class="tech.availability === 'Available' ? 'bg-green-50 border-green-200 text-green-600' : 'bg-yellow-50 border-yellow-200 text-yellow-600'">
                    {{ tech.availability }}
                  </div>
                </div>
              </div>

              <h3 class="text-sm font-bold text-gray-900 mb-3">Task Details</h3>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Maintenance Task</p>
                  <select v-model="assignForm.task" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                    <option value="">Select task</option>
                    <option v-for="t in openTasks" :key="t.name" :value="t.name">
                      {{ t.name }}{{ t.task_description ? ` — ${t.task_description}` : '' }}
                    </option>
                  </select>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Priority</p>
                  <select v-model="assignForm.priority" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                    <option value="Urgent">Urgent</option>
                    <option value="High">High</option>
                    <option value="Normal">Normal</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Task Type</p>
                  <select v-model="assignForm.task_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                    <option value="Corrective Maintenance">Corrective Maintenance</option>
                    <option value="Preventive Maintenance">Preventive Maintenance</option>
                    <option value="Inspection">Inspection</option>
                  </select>
                </div>
              </div>

              <div class="mb-4">
                <p class="text-xs text-gray-500 mb-1.5">Assignment Note</p>
                <textarea v-model="assignForm.note" rows="3"
                  placeholder="Technician instructions, access note, expected caution, or troubleshooting direction..."
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
              </div>

              <!-- Summary cards -->
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
                <div class="bg-gray-50 rounded-xl border border-gray-100 p-3">
                  <p class="text-xs text-gray-400 mb-1">Open Assignments</p>
                  <p class="text-sm font-bold text-gray-900">{{ tech.open_tasks_count }} active</p>
                </div>
                <div class="bg-gray-50 rounded-xl border border-gray-100 p-3">
                  <p class="text-xs text-gray-400 mb-1">Completion Score</p>
                  <p class="text-sm font-bold text-gray-900">{{ tech.completion_score }}%</p>
                </div>
                <div class="bg-blue-50 rounded-xl border border-blue-100 p-3">
                  <p class="text-xs text-blue-500 mb-1">Specialization</p>
                  <p class="text-xs font-bold text-blue-700">{{ tech.primary_specialization || 'General' }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Teleport>

    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const route = useRoute()
const techId = route.params.id

const loading = ref(true)
const loadError = ref(null)
const tech = ref(null)
const editMode = ref(false)
const saving = ref(false)
const updatingAvailability = ref(false)
const showAssignModal = ref(false)
const assigning = ref(false)
const editForm = ref({})
const employees = ref([])
const suppliers = ref([])
const openTasks = ref([])

const assignForm = ref({
  task: '',
  priority: 'Normal',
  task_type: 'Corrective Maintenance',
  note: ''
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

// ─── Load technician ──────────────────────────────────────────────────────────
const techResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.technician.get_technician',
  auto: false
})

async function loadTechnician() {
  loading.value = true
  loadError.value = null
  try {
    const res = await techResource.fetch({ technician_id: techId })
    console.log('[TechnicianView] get_technician:', res)
    tech.value = res
  } catch (e) {
    console.error('[TechnicianView] load error:', e)
    loadError.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

// ─── Load dropdown data for edit mode ────────────────────────────────────────
const empResource = createResource({ url: 'rhohotel.rhocom_hotel.api.technician.get_employees_for_technician', auto: false })
const supResource = createResource({ url: 'rhohotel.rhocom_hotel.api.technician.get_vendors_for_technician', auto: false })
const openTasksResource = createResource({ url: 'rhohotel.rhocom_hotel.api.technician.get_open_maintenance_tasks', auto: false })

async function loadDropdowns() {
  const [empRes, supRes, taskRes] = await Promise.all([
    empResource.fetch(),
    supResource.fetch(),
    openTasksResource.fetch()
  ])
  employees.value = empRes || []
  suppliers.value = supRes || []
  openTasks.value = taskRes || []
}

// ─── Edit mode ────────────────────────────────────────────────────────────────
function enterEditMode() {
  editForm.value = {
    technician_name: tech.value.technician_name,
    technician_type: tech.value.technician_type,
    availability: tech.value.availability,
    employee: tech.value.employee || '',
    supplier: tech.value.supplier || '',
    primary_specialization: tech.value.primary_specialization || '',
    secondary_skills: tech.value.secondary_skills || '',
    phone: tech.value.phone || '',
    email: tech.value.email || '',
    shift: tech.value.shift || '',
    response_priority_group: tech.value.response_priority_group || 'Standard',
    can_receive_urgent: !!tech.value.can_receive_urgent,
    visible_for_assignment: !!tech.value.visible_for_assignment,
    notes: tech.value.notes || '',
    supported_categories: tech.value.supported_categories || '',
    certification: tech.value.certification || '',
  }
  if (!employees.value.length) loadDropdowns()
  editMode.value = true
}

function cancelEdit() {
  editMode.value = false
  editForm.value = {}
}

function onEditEmployeeSelect() {
  const emp = employees.value.find(e => e.name === editForm.value.employee)
  if (!emp) return
  if (!editForm.value.technician_name) editForm.value.technician_name = emp.employee_name
  if (!editForm.value.phone && emp.cell_number) editForm.value.phone = emp.cell_number
  if (!editForm.value.email && emp.personal_email) editForm.value.email = emp.personal_email
}

function onEditSupplierSelect() {
  const sup = suppliers.value.find(s => s.name === editForm.value.supplier)
  if (!sup) return
  if (!editForm.value.technician_name) editForm.value.technician_name = sup.supplier_name
  if (!editForm.value.phone && sup.mobile_no) editForm.value.phone = sup.mobile_no
  if (!editForm.value.email && sup.email_id) editForm.value.email = sup.email_id
}

const updateResource = createResource({ url: 'rhohotel.rhocom_hotel.api.technician.update_technician', auto: false })

async function saveEdit() {
  if (!editForm.value.technician_name?.trim()) { showToast('Technician name is required'); return }
  saving.value = true
  try {
    const res = await updateResource.fetch({ technician_id: techId, technician_data: editForm.value })
    console.log('[TechnicianView] update_technician:', res)
    if (res?.success) {
      showToast('Profile updated', 'success')
      editMode.value = false
      await loadTechnician()
    } else {
      showToast('Failed to update: ' + (res?.error || 'Unknown error'))
    }
  } catch (e) {
    console.error('[TechnicianView] save error:', e)
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    saving.value = false
  }
}

// ─── Assign existing task to this technician ──────────────────────────────────
const assignTaskResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.technician.assign_task_to_technician',
  auto: false
})

async function assignTask() {
  if (!assignForm.value.task) { showToast('Please select a task'); return }
  assigning.value = true
  try {
    const res = await assignTaskResource.fetch({
      task_name: assignForm.value.task,
      technician_id: techId,
      note: assignForm.value.note
    })
    console.log('[TechnicianView] assignTask:', res)
    if (res?.success) {
      showToast('Task assigned successfully', 'success')
      showAssignModal.value = false
      assignForm.value = { task: '', priority: 'Normal', task_type: 'Corrective Maintenance', note: '' }
      await loadTechnician() // refresh open task count + list
    } else {
      showToast('Failed to assign: ' + (res?.error || 'Unknown error'))
    }
  } catch (e) {
    console.error('[TechnicianView] assignTask error:', e)
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    assigning.value = false
  }
}

// ─── Availability quick toggle ────────────────────────────────────────────────
const availResource = createResource({ url: 'rhohotel.rhocom_hotel.api.technician.update_availability', auto: false })

async function setAvailability(value) {
  updatingAvailability.value = true
  try {
    const res = await availResource.fetch({ technician_id: techId, availability: value })
    if (res?.success) {
      tech.value.availability = value
      showToast(`Marked as ${value}`, 'success')
    } else {
      showToast('Failed to update availability: ' + (res?.error || ''))
    }
  } catch (e) {
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    updatingAvailability.value = false
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function availabilityBadgeClass(a) {
  return {
    'Available':   'bg-green-100 text-green-600',
    'On Call':     'bg-yellow-100 text-yellow-600',
    'Unavailable': 'bg-gray-100 text-gray-500',
  }[a] || 'bg-gray-100 text-gray-500'
}

function availabilityTextClass(a) {
  return {
    'Available':   'text-green-600',
    'On Call':     'text-yellow-600',
    'Unavailable': 'text-gray-400',
  }[a] || ''
}

function taskStatusClass(s) {
  return {
    'Open':        'bg-blue-100 text-blue-600',
    'In Progress': 'bg-yellow-100 text-yellow-600',
    'Assigned':    'bg-purple-100 text-purple-600',
    'Pending':     'bg-gray-100 text-gray-500',
  }[s] || 'bg-gray-100 text-gray-500'
}

function priorityClass(p) {
  return {
    'Urgent': 'bg-red-100 text-red-500',
    'High':   'bg-orange-100 text-orange-500',
    'Normal': 'bg-gray-100 text-gray-500',
    'Low':    'bg-green-100 text-green-600',
  }[p] || 'bg-gray-100 text-gray-500'
}

// ─── Init ─────────────────────────────────────────────────────────────────────
onMounted(() => {
  loadTechnician()
  loadDropdowns() // pre-fetch so assign modal is ready immediately
})
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>