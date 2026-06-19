<template>
  <div class="space-y-5">

    <!-- Toast -->
    <div
      v-if="showToast"
      class="fixed top-5 right-5 z-[60] text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-lg"
      :class="toastType === 'error' ? 'bg-red-600' : 'bg-green-600'"
    >
      {{ toastMessage }}
    </div>

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">View every staff member's Shift Type for each day of the week. Use the Shift Assignment Tool to assign shifts, or AI Auto Assign to preview a balanced roster.</p>
    </div>

    <!-- Weekly Roster Control -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Weekly Roster Control</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">Select a department and week. Every active staff member in that department is shown with their Shift Type and time for each day.</p>

      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Department</p>
          <select v-model="department" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option v-if="!departmentOptions.length" value="">Loading...</option>
            <option v-for="dept in departmentOptions" :key="dept" :value="dept">{{ dept }}</option>
          </select>
        </div>
        <div style="min-width:200px;">
          <p class="text-xs text-gray-500 mb-1.5">Week Starting</p>
          <div class="flex items-center gap-2">
            <button
              class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              @click="changeWeek(-1)">&lsaquo;</button>
            <input v-model="weekStartInput" type="date"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white" />
            <button
              class="px-2.5 py-2.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              @click="changeWeek(1)">&rsaquo;</button>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2 flex-wrap mt-4">
        <span v-if="error" class="text-xs text-red-500 mr-2">{{ error }}</span>
        <span v-if="message" class="text-xs mr-2" :class="messageType === 'error' ? 'text-red-500' : 'text-green-600'">{{ message }}</span>

        <div class="flex items-center gap-1 p-1 bg-gray-100 rounded-lg">
          <button
            class="px-3 py-1.5 text-xs font-semibold rounded-md transition-colors"
            :class="viewMode === 'draft' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            @click="switchView('draft')">Draft / Edit</button>
          <button
            class="px-3 py-1.5 text-xs font-semibold rounded-md transition-colors"
            :class="viewMode === 'roster' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            @click="switchView('roster')">Roster View</button>
        </div>

        <button
          class="px-4 py-2.5 text-xs font-semibold text-sky-700 bg-sky-50 border border-sky-200 rounded-lg hover:bg-sky-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading"
          @click="openAssignmentTool">Shift Assignment Tool</button>
        <button
          class="px-4 py-2.5 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading"
          @click="openAddShiftType">Add Shift Type</button>
        <button
          class="px-4 py-2.5 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading"
          @click="openViewShiftTypes">View All Shift Types</button>


          
        <button
          class="px-4 py-2.5 text-xs font-semibold text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          style="background: linear-gradient(90deg, #8b5cf6, #6366f1);"
          :disabled="loading || aiRunning"
          @click="aiAutoAssign">{{ aiRunning ? 'Generating...' : 'AI Auto Assign' }}</button>

        <template v-if="viewMode === 'draft'">
          <button
            class="px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="loading || saving || !isDraftDirty"
            @click="saveDraft">{{ saving === 'draft' ? 'Saving...' : 'Save Draft' }}</button>
          <button
            class="px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="loading || saving || (!isDraftDirty && !hasDraft)"
            @click="publishDraft">{{ saving === 'publish' ? 'Publishing...' : 'Publish' }}</button>
        </template>
        <button
          v-else
          class="px-4 bg-blue-600 text-white py-2.5 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading"
          @click="loadRoster">Refresh</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Department Staff</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Active</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : staffList.length }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Assigned Slots</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="assignedSlotsBadgeClass">{{ assignedSlotsBadgeLabel }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : `${assignedSlots} / ${totalSlots}` }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Coverage Level</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="coverageBadgeClass">{{ coverageLabel }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : `${coverageLevel}%` }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Conflict Alerts</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="conflictAlerts > 0 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'">{{ conflictAlerts > 0 ? 'Review' : 'Clear' }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ loading ? '...' : conflictAlerts }}</p>
      </div>
    </div>

    <!-- Weekly Draft Editor -->
    <div v-if="viewMode === 'draft'" class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Weekly Draft Editor{{ previewMode ? ' - AI Preview' : '' }}</h3>
          <p class="text-xs text-gray-400 mt-0.5">{{ department || '...' }} &bull; {{ weekRangeLabel }}</p>
        </div>
        <button
          v-if="previewMode"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="loadDraft">Exit Preview</button>
      </div>

      <div class="px-6 py-4 overflow-x-auto">
        <div v-if="loading" class="py-12 text-center text-xs text-gray-400">Loading draft shifts for {{ department || 'department' }} &bull; week of {{ weekRangeLabel }}...</div>
        <div v-else-if="!staffList.length" class="py-12 text-center text-xs text-gray-400">No staff found for this department.</div>
        <template v-else>
          <div v-if="!hasDraft && !previewMode" class="mb-4 px-4 py-2.5 text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-lg">
            No draft shifts found for this week. Every staff member defaults to OFF below &mdash; assign shifts and click "Save Draft" or "Publish".
          </div>

          <table class="w-full border-collapse" style="min-width:1200px;">
            <thead>
              <tr class="bg-gray-50">
                <th class="text-left px-3 py-2.5 text-xs font-semibold text-black rounded-l-lg" style="min-width:180px;">Staff / Role</th>
                <th v-for="day in days" :key="day.label" class="text-left px-3 py-2.5" style="min-width:150px;">
                  <p class="text-xs font-semibold text-gray-700">{{ day.label }}</p>
                  <p class="text-xs text-gray-400">{{ day.dateLabel }}</p>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="staff in staffList" :key="staff.id" class="border-b border-gray-100">
                <td class="px-3 py-3 align-top">
                  <p class="text-sm font-bold text-gray-900">{{ staff.name }}</p>
                  <p class="text-xs text-gray-400">{{ staff.role }}<span v-if="staff.area"> &bull; {{ staff.area }}</span></p>
                </td>
                <td v-for="day in days" :key="day.label" class="px-3 py-2.5 align-top">
                  <div class="relative">
                    <select
                      v-model="staff.shifts[day.date].value"
                      :disabled="isLocked(staff.shifts[day.date])"
                      :class="['w-full appearance-none px-3 py-1.5 pr-7 text-xs font-semibold rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-200', isLocked(staff.shifts[day.date]) ? 'cursor-not-allowed opacity-75' : 'cursor-pointer', shiftClass(staff.shifts[day.date].value, staff.shifts[day.date])]"
                    >
                      <option v-for="opt in shiftTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                    </select>
                    <ChevronDown class="w-3.5 h-3.5 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" :class="chevronClass(staff.shifts[day.date].value, staff.shifts[day.date])" />
                  </div>
                  <p v-if="isLocked(staff.shifts[day.date])" class="text-xs text-gray-400 mt-1">Published &bull; locked</p>
                  <p v-else-if="staff.shifts[day.date].draft" class="text-xs text-amber-600 mt-1">Draft &bull; not published</p>
                  <p v-else-if="staff.shifts[day.date].value === 'OFF'" class="text-xs text-gray-400 mt-1">No shift assigned</p>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Legend -->
          <div class="flex items-center gap-6 flex-wrap mt-5 pt-4 border-t border-gray-100">
            <div v-for="opt in shiftLegend" :key="opt.color" class="flex items-center gap-2">
              <span class="w-4 h-4 rounded" :class="opt.swatchClass"></span>
              <span class="text-xs text-gray-500">{{ opt.label }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-4 h-4 rounded bg-gray-100 ring-2 ring-amber-400 ring-offset-1"></span>
              <span class="text-xs text-gray-500">Draft (unpublished change)</span>
            </div>
            <div class="flex-1"></div>
            <p class="text-xs text-gray-400">Published shifts are locked &bull; amber outline = unpublished draft</p>
          </div>
        </template>
      </div>
    </div>

    <!-- Weekly Roaster Calendar -->
    <div v-else class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Weekly Roaster Calendar{{ previewMode ? ' - AI Preview' : '' }}</h3>
          <p class="text-xs text-gray-400 mt-0.5">{{ department || '...' }} &bull; {{ weekRangeLabel }}</p>
        </div>
        <button
          v-if="previewMode"
          class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="loadRoster">Exit Preview</button>
      </div>

      <div class="px-6 py-4 overflow-x-auto">
        <div v-if="loading" class="py-12 text-center text-xs text-gray-400">Loading staff for {{ department || 'department' }}...</div>
        <div v-else-if="!staffList.length" class="py-12 text-center text-xs text-gray-400">No staff found for this department.</div>
        <table v-else class="w-full border-collapse" style="min-width:1200px;">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg" style="min-width:180px;">Staff / Role</th>
              <th v-for="day in days" :key="day.label" class="text-left px-3 py-2.5" style="min-width:150px;">
                <p class="text-xs font-semibold text-gray-700">{{ day.label }}</p>
                <p class="text-xs text-gray-400">{{ day.dateLabel }}</p>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="staff in staffList" :key="staff.id" class="border-b border-gray-100">
              <td class="px-3 py-3 align-top">
                <p class="text-sm font-bold text-gray-900">{{ staff.name }}</p>
                <p class="text-xs text-gray-400">{{ staff.role }}<span v-if="staff.area"> &bull; {{ staff.area }}</span></p>
              </td>
              <td v-for="day in days" :key="day.label" class="px-2 py-2.5 align-top">
                <div class="cal-event" :class="eventColor(staff.shifts[day.date])">
                  <p class="text-xs font-bold leading-tight">{{ eventLabel(staff.shifts[day.date]) }}</p>
                  <p v-if="staff.shifts[day.date].time" class="text-xs opacity-75 mt-0.5">{{ staff.shifts[day.date].time }}</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Legend -->
        <div class="flex items-center gap-5 mt-5 pt-4 border-t border-gray-100 flex-wrap">
          <div v-for="entry in legendEntries" :key="entry.color" class="flex items-center gap-1.5 text-xs text-gray-500">
            <span class="w-3 h-3 rounded inline-block" :class="entry.color"></span> {{ entry.label }}
          </div>
        </div>
      </div>
    </div>

    <!-- AI Auto Assign Intelligence -->
    <div class="rounded-xl border px-6 py-4" style="background:#f5f3ff; border-color:#e9d5ff;">
      <h3 class="text-sm font-bold" style="color:#7c3aed;">AI Auto Assign Intelligence</h3>
      <p class="text-xs mt-1" style="color:#8b5cf6;">Uses staff availability, leave days, previous shifts, overtime rules, weekend rotation, department coverage rules, and conflict detection to preview a balanced weekly roster. Use the Shift Assignment Tool to apply changes.</p>
    </div>

    <!-- Shift Assignment Tool Modal -->
    <Teleport to="body" v-if="showAssignmentTool">
      <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
        style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
        @click.self="closeAssignmentTool">
        <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:820px;max-height:92vh;">

          <!-- Header -->
          <div class="px-8 pt-7 pb-5 flex items-start justify-between border-b border-gray-100">
            <div>
              <h2 class="text-2xl font-bold text-gray-900">Shift Assignment Tool</h2>
              <p class="text-xs text-gray-400 mt-1">Assign a Shift Type to one or more employees for a date range.</p>
            </div>
            <button @click="closeAssignmentTool"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex-shrink-0">Close</button>
          </div>

          <div class="px-8 py-6 space-y-5">

            <div v-if="toolMessage" class="px-3 py-2 text-xs rounded-lg" :class="toolMessageType === 'error' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'">
              {{ toolMessage }}
            </div>

            <!-- Shift Assignment Details -->
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Shift Assignment Details</h3>
              <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Action</p>
                  <select v-model="toolForm.action" disabled class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-500 bg-gray-50">
                    <option>Assign Shift</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Company</p>
                  <input :value="toolForm.company" disabled type="text"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-500 bg-gray-50" />
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Shift Type <span class="text-red-500">*</span></p>
                  <select v-model="toolForm.shift_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700">
                    <option value="">Select shift type</option>
                    <option v-for="s in toolOptions.shift_types" :key="s" :value="s">{{ s }}</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Status</p>
                  <select v-model="toolForm.status" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700">
                    <option value="Active">Active</option>
                    <option value="Inactive">Inactive</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Start Date <span class="text-red-500">*</span></p>
                  <input v-model="toolForm.start_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700" />
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">End Date</p>
                  <input v-model="toolForm.end_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700" />
                </div>
              </div>
            </div>

            <!-- Quick Filters -->
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Quick Filters</h3>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Department</p>
                  <select v-model="toolForm.department" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700">
                    <option value="">All</option>
                    <option v-for="d in toolOptions.departments" :key="d" :value="d">{{ d }}</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Branch</p>
                  <select v-model="toolForm.branch" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700">
                    <option value="">All</option>
                    <option v-for="b in toolOptions.branches" :key="b" :value="b">{{ b }}</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Designation</p>
                  <select v-model="toolForm.designation" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700">
                    <option value="">All</option>
                    <option v-for="d in toolOptions.designations" :key="d" :value="d">{{ d }}</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Employee Grade</p>
                  <select v-model="toolForm.grade" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700">
                    <option value="">All</option>
                    <option v-for="g in toolOptions.grades" :key="g" :value="g">{{ g }}</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Employment Type</p>
                  <select v-model="toolForm.employment_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700">
                    <option value="">All</option>
                    <option v-for="e in toolOptions.employment_types" :key="e" :value="e">{{ e }}</option>
                  </select>
                </div>
                <div class="flex items-end">
                  <button
                    class="w-full px-4 py-2.5 text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="!canSearchEmployees || loadingEmployees"
                    @click="searchEmployees">{{ loadingEmployees ? 'Searching...' : 'Search Employees' }}</button>
                </div>
              </div>
            </div>

            <!-- Select Employees -->
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <div class="flex items-center justify-between mb-3">
                <h3 class="text-sm font-bold text-gray-900">Select Employees</h3>
                <label class="flex items-center gap-2 text-xs text-gray-500 cursor-pointer">
                  <input type="checkbox" :checked="allSelected" @change="toggleSelectAll" />
                  Select all
                </label>
              </div>

              <div v-if="!eligibleEmployees.length" class="py-6 text-center text-xs text-gray-400">
                {{ employeeListMessage }}
              </div>
              <div v-else class="border border-gray-100 rounded-lg overflow-hidden">
                <table class="w-full border-collapse">
                  <thead>
                    <tr class="bg-gray-50">
                      <th class="text-left px-3 py-2 text-xs font-semibold text-gray-500" style="width:36px;"></th>
                      <th class="text-left px-3 py-2 text-xs font-semibold text-gray-500">Employee</th>
                      <th class="text-left px-3 py-2 text-xs font-semibold text-gray-500">Employee Name</th>
                      <th class="text-left px-3 py-2 text-xs font-semibold text-gray-500">Branch</th>
                      <th class="text-left px-3 py-2 text-xs font-semibold text-gray-500">Department</th>
                      <th class="text-left px-3 py-2 text-xs font-semibold text-gray-500">Default Shift</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="emp in eligibleEmployees" :key="emp.employee" class="border-t border-gray-100">
                      <td class="px-3 py-2">
                        <input type="checkbox" v-model="selectedEmployees" :value="emp.employee" />
                      </td>
                      <td class="px-3 py-2 text-xs font-semibold text-gray-900">{{ emp.employee }}</td>
                      <td class="px-3 py-2 text-xs text-gray-700">{{ emp.employee_name }}</td>
                      <td class="px-3 py-2 text-xs text-gray-500">{{ emp.branch || '—' }}</td>
                      <td class="px-3 py-2 text-xs text-gray-500">{{ emp.department || '—' }}</td>
                      <td class="px-3 py-2 text-xs text-gray-500">{{ emp.default_shift || '—' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="text-xs text-gray-400 mt-2">{{ selectedEmployees.length }} employee(s) selected</p>
            </div>

          </div>

          <!-- Footer Actions -->
          <div class="px-8 py-5 bg-gray-50 border-t border-gray-100 flex items-center justify-end gap-3">
            <button
              class="px-6 py-2.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="closeAssignmentTool">Cancel</button>
            <button
              class="px-6 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!canAssign || assigning"
              @click="assignShift">{{ assigning ? 'Assigning...' : 'Assign Shift' }}</button>
          </div>

        </div>
      </div>
    </Teleport>

    <!-- Add Shift Type Modal -->
    <Teleport to="body" v-if="showAddShiftType">
      <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
        style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
        @click.self="closeAddShiftType">
        <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:560px;max-height:92vh;">

          <!-- Header -->
          <div class="px-8 pt-7 pb-5 flex items-start justify-between border-b border-gray-100">
            <div>
              <h2 class="text-2xl font-bold text-gray-900">Add Shift Type</h2>
              <p class="text-xs text-gray-400 mt-1">Create a new Shift Type for use across the weekly roster and shift assignments.</p>
            </div>
            <button @click="closeAddShiftType"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex-shrink-0">Close</button>
          </div>

          <div class="px-8 py-6 space-y-5">

            <div v-if="shiftTypeMessage" class="px-3 py-2 text-xs rounded-lg" :class="shiftTypeMessageType === 'error' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'">
              {{ shiftTypeMessage }}
            </div>

            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Shift Type Details</h3>
              <div class="space-y-4">
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Name <span class="text-red-500">*</span></p>
                  <input v-model="shiftTypeForm.name" type="text" placeholder="e.g. Morning, Afternoon, Night, Supervisor"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700" />
                </div>
                <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
                  <div>
                    <p class="text-xs font-semibold text-gray-700 mb-1.5">Start Time <span class="text-red-500">*</span></p>
                    <input v-model="shiftTypeForm.start_time" type="time"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700" />
                  </div>
                  <div>
                    <p class="text-xs font-semibold text-gray-700 mb-1.5">End Time <span class="text-red-500">*</span></p>
                    <input v-model="shiftTypeForm.end_time" type="time"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700" />
                  </div>
                </div>
                <p class="text-xs text-gray-400">If End Time is earlier than Start Time, the shift is treated as an overnight shift (e.g. Night: 22:00 - 06:00).</p>
              </div>
            </div>

          </div>

          <!-- Footer Actions -->
          <div class="px-8 py-5 bg-gray-50 border-t border-gray-100 flex items-center justify-end gap-3">
            <button
              class="px-6 py-2.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="closeAddShiftType">Cancel</button>
            <button
              class="px-6 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!canCreateShiftType || creatingShiftType"
              @click="createShiftType">{{ creatingShiftType ? 'Adding...' : 'Add Shift Type' }}</button>
          </div>

        </div>
      </div>
    </Teleport>

    <!-- View All Shift Types Modal -->
    <Teleport to="body" v-if="showViewShiftTypes">
      <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
        style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
        @click.self="closeViewShiftTypes">
        <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:600px;max-height:92vh;">

          <!-- Header -->
          <div class="px-8 pt-7 pb-5 flex items-start justify-between border-b border-gray-100">
            <div>
              <h2 class="text-2xl font-bold text-gray-900">All Shift Types</h2>
              <p class="text-xs text-gray-400 mt-1">View every Shift Type and its time range. Click Edit on a row to change its time.</p>
            </div>
            <button @click="closeViewShiftTypes"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex-shrink-0">Close</button>
          </div>

          <div class="px-8 py-6">

            <div v-if="loadingShiftTypeList" class="py-10 text-center text-xs text-gray-400">Loading Shift Types...</div>
            <div v-else-if="!allShiftTypes.length" class="py-10 text-center text-xs text-gray-400">No Shift Types found.</div>

            <div v-else class="border border-gray-100 rounded-lg overflow-hidden">
              <table class="w-full border-collapse">
                <thead>
                  <tr class="bg-gray-50">
                    <th class="text-left px-3 py-2 text-xs font-semibold text-gray-500">Name</th>
                    <th class="text-left px-3 py-2 text-xs font-semibold text-gray-500">Time</th>
                    <th class="text-left px-3 py-2 text-xs font-semibold text-gray-500">In Use</th>
                    <th class="text-left px-3 py-2 text-xs font-semibold text-gray-500" style="width:80px;"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="st in allShiftTypes" :key="st.name" class="border-t border-gray-100">
                    <td class="px-3 py-2.5 text-xs font-semibold text-gray-900">{{ st.name }}</td>
                    <td class="px-3 py-2.5 text-xs text-gray-600">{{ st.time_label || '—' }}</td>
                    <td class="px-3 py-2.5 text-xs text-gray-500">{{ st.in_use_count }} assignment(s)</td>
                    <td class="px-3 py-2.5">
                      <button
                        class="px-3 py-1 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                        @click="openEditShiftType(st)">Edit</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

          </div>

        </div>
      </div>
    </Teleport>

    <!-- Edit Shift Type Modal -->
    <Teleport to="body" v-if="showEditShiftType">
      <div class="fixed inset-0 z-[55] flex items-center justify-center p-6"
        style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
        @click.self="closeEditShiftType">
        <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:480px;max-height:92vh;">

          <!-- Header -->
          <div class="px-8 pt-7 pb-5 flex items-start justify-between border-b border-gray-100">
            <div>
              <h2 class="text-2xl font-bold text-gray-900">Edit Shift Type</h2>
              <p class="text-xs text-gray-400 mt-1">{{ editShiftTypeForm.name }}</p>
            </div>
            <button @click="closeEditShiftType"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex-shrink-0">Close</button>
          </div>

          <div class="px-8 py-6 space-y-5">

            <div v-if="editShiftTypeMessage" class="px-3 py-2 text-xs rounded-lg" :class="editShiftTypeMessageType === 'error' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'">
              {{ editShiftTypeMessage }}
            </div>

            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Shift Type Details</h3>
              <div class="space-y-4">
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Name</p>
                  <input :value="editShiftTypeForm.name" disabled type="text"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg text-gray-500 bg-gray-50" />
                  <p class="text-xs text-gray-400 mt-1">Renaming a Shift Type isn't supported here.</p>
                </div>
                <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
                  <div>
                    <p class="text-xs font-semibold text-gray-700 mb-1.5">Start Time <span class="text-red-500">*</span></p>
                    <input v-model="editShiftTypeForm.start_time" type="time"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700" />
                  </div>
                  <div>
                    <p class="text-xs font-semibold text-gray-700 mb-1.5">End Time <span class="text-red-500">*</span></p>
                    <input v-model="editShiftTypeForm.end_time" type="time"
                      class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 text-gray-700" />
                  </div>
                </div>
                <p class="text-xs text-gray-400">If End Time is earlier than Start Time, the shift is treated as an overnight shift (e.g. Night: 22:00 - 06:00).</p>
              </div>
            </div>

          </div>

          <!-- Footer Actions -->
          <div class="px-8 py-5 bg-gray-50 border-t border-gray-100 flex items-center justify-end gap-3">
            <button
              class="px-6 py-2.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="closeEditShiftType">Cancel</button>
            <button
              class="px-6 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!canSaveEditShiftType || savingEditShiftType"
              @click="saveEditShiftType">{{ savingEditShiftType ? 'Saving...' : 'Save Changes' }}</button>
          </div>

        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'

// ---------------------------------------------------------------------------
// API contract (rhohotel.rhocom_hotel.api.weekly_shift_generator):
//
// get_departments() -> ["Housekeeping", "Front Desk", ...]
//
// get_weekly_roster(department, week_start) -> {
//   staff: [
//     { employee, employee_name, designation, area,
//       shifts: { "2026-04-12": { shift_type, status, time }, ... } }
//   ],
//   stats: { coverage_level, conflict_alerts, total_slots, assigned_slots }
// }
//   shift_type is always the real Shift Type name (or "OFF" when no
//   assignment exists). status is "Active" | "Off" | "Leave" -- "Leave"
//   means the underlying Shift Assignment is Inactive, but it no longer
//   changes the displayed label or color, both of which are driven purely
//   by shift_type. time is "hh:mm A - hh:mm A" or "".
//
// ai_auto_assign(department, week_start) -> same shape as get_weekly_roster
//   (preview only, does not write to the database)
//
// get_assignment_tool_options() -> {
//   companies, shift_types, branches, designations, employment_types,
//   grades, departments, default_company
// }
//
// get_assignment_tool_employees(company, branch, department, designation,
//   grade, employment_type, shift_type, start_date, end_date, status)
//   -> [{ employee, employee_name, branch, department, designation, default_shift }]
//
// bulk_assign_shift(employees, company, shift_type, start_date, end_date, status)
//   -> { success: [...], failure: [...] }
// ---------------------------------------------------------------------------

const departmentOptions = ref([])
const department = ref('')
const viewMode = ref('draft')
const hasDraft = ref(false)
const draftSnapshot = ref('')

const days = ref([])
const staffList = ref([])
const serverStats = ref(null)
const previewMode = ref(false)
const shiftTypeOptions = ref([
  { value: 'OFF', label: 'OFF' },
])

const loading = ref(false)
const aiRunning = ref(false)
const error = ref('')
const message = ref('')
const messageType = ref('success')

const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('success')
let toastTimer = null

function showToastMessage(text, type = 'success') {
  toastMessage.value = text
  toastType.value = type
  showToast.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { showToast.value = false }, 3200)
}

const DAY_FORMAT = new Intl.DateTimeFormat('en-US', { weekday: 'long' })
const DATE_LABEL_FORMAT = new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short' })
const FULL_DATE_FORMAT = new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })

function isoDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function startOfWeek(date) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day // ISO week starts on Monday
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

const weekStart = ref(startOfWeek(new Date()))
const weekStartInput = computed({
  get: () => isoDate(weekStart.value),
  set: (val) => {
    if (!val) return
    weekStart.value = startOfWeek(new Date(val))
  },
})

const weekRangeLabel = computed(() => {
  if (!days.value.length) return ''
  const start = new Date(weekStart.value)
  const end = new Date(weekStart.value)
  end.setDate(end.getDate() + 6)
  return `${FULL_DATE_FORMAT.format(start)} - ${FULL_DATE_FORMAT.format(end)}`
})

function buildDays() {
  days.value = Array.from({ length: 7 }, (_, idx) => {
    const d = new Date(weekStart.value)
    d.setDate(d.getDate() + idx)
    return {
      label: DAY_FORMAT.format(d),
      date: isoDate(d),
      dateLabel: DATE_LABEL_FORMAT.format(d),
    }
  })
}
buildDays()

function changeWeek(deltaWeeks) {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + deltaWeeks * 7)
  weekStart.value = d
}

// ---------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------

async function loadDepartments() {
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.get_departments')
    departmentOptions.value = result || []
    if (!department.value && departmentOptions.value.length) {
      department.value = departmentOptions.value[0]
    }
  } catch (err) {
    error.value = err.message || 'Failed to load departments.'
  }
}

function mapRosterRow(row) {
  return {
    id: row.employee,
    name: row.employee_name || row.employee,
    role: row.designation || '—',
    area: row.area || '',
    shifts: row.shifts || {},
  }
}

function mapDraftRow(row) {
  return {
    id: row.employee,
    name: row.employee_name || row.employee,
    role: row.designation || '—',
    area: row.area || '',
    shifts: row.shifts || {},
  }
}

async function loadRoster() {
  if (!department.value) return
  loading.value = true
  error.value = ''
  message.value = ''
  previewMode.value = false
  buildDays()
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.get_weekly_roster', {
      department: department.value,
      week_start: isoDate(weekStart.value),
    })
    staffList.value = (result?.staff || []).map(mapRosterRow)
    serverStats.value = result?.stats || null
  } catch (err) {
    error.value = err.message || 'Failed to load weekly roster.'
    staffList.value = []
  } finally {
    loading.value = false
  }
}

async function loadDraft() {
  if (!department.value) return
  loading.value = true
  error.value = ''
  message.value = ''
  previewMode.value = false
  buildDays()
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.get_weekly_draft', {
      department: department.value,
      week_start: isoDate(weekStart.value),
    })
    staffList.value = (result?.staff || []).map(mapDraftRow)
    serverStats.value = result?.stats || null
    hasDraft.value = Boolean(result?.has_draft)
    draftSnapshot.value = JSON.stringify(buildDraftAssignments())
  } catch (err) {
    error.value = err.message || 'Failed to load draft shifts.'
    staffList.value = []
  } finally {
    loading.value = false
  }
}

function refreshData() {
  return viewMode.value === 'draft' ? loadDraft() : loadRoster()
}

function switchView(mode) {
  if (viewMode.value === mode) return
  viewMode.value = mode
  refreshData()
}

function buildDraftAssignments() {
  const assignments = {}
  staffList.value.forEach((staff) => {
    const dayMap = {}
    days.value.forEach((day) => {
      dayMap[day.date] = staff.shifts[day.date]?.value || 'OFF'
    })
    assignments[staff.id] = dayMap
  })
  return assignments
}

// Only includes employee/day entries whose value actually differs from the
// last-loaded baseline (draftSnapshot). Sending the full grid on every
// save/publish caused already-published, unchanged multi-day Shift
// Assignment records to be needlessly re-processed (split/recreated) by
// the backend, which could collide with itself and trigger HRMS's native
// "already has an active Shift Assignment" conflict for days that were
// never actually touched in this session.
function buildChangedAssignments() {
  const current = buildDraftAssignments()
  let baseline = {}
  try {
    baseline = draftSnapshot.value ? JSON.parse(draftSnapshot.value) : {}
  } catch (e) {
    baseline = {}
  }

  const changed = {}
  Object.keys(current).forEach((staffId) => {
    const currentDayMap = current[staffId] || {}
    const baselineDayMap = baseline[staffId] || {}
    const changedDays = {}

    Object.keys(currentDayMap).forEach((date) => {
      const currentValue = currentDayMap[date]
      const baselineValue = baselineDayMap[date] !== undefined ? baselineDayMap[date] : 'OFF'
      if (currentValue !== baselineValue) {
        changedDays[date] = currentValue
      }
    })

    if (Object.keys(changedDays).length) {
      changed[staffId] = changedDays
    }
  })

  return changed
}

// Publish needs more than "what changed in this editing session" --
// it also needs every cell that's already saved as an unpublished draft
// (docstatus=0), since a prior Save Draft call refreshes draftSnapshot to
// match the saved state, which would otherwise make buildChangedAssignments()
// return an empty diff and silently publish nothing. This merges genuinely
// new edits with every cell currently flagged staff.shifts[date].draft.
function buildPublishAssignments() {
  const merged = buildChangedAssignments()

  staffList.value.forEach((staff) => {
    days.value.forEach((day) => {
      const cell = staff.shifts[day.date]
      if (!cell?.draft) return

      if (!merged[staff.id]) merged[staff.id] = {}
      if (merged[staff.id][day.date] === undefined) {
        merged[staff.id][day.date] = cell.value || 'OFF'
      }
    })
  })

  return merged
}

const isDraftDirty = computed(() => JSON.stringify(buildDraftAssignments()) !== draftSnapshot.value)

const saving = ref('')

async function saveDraft() {
  saving.value = 'draft'
  message.value = ''
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.save_weekly_draft', {
      department: department.value,
      week_start: isoDate(weekStart.value),
      assignments: buildChangedAssignments(),
    })
    await loadDraft()
    const warnings = result?.warnings || []
    if (warnings.length) {
      showToastMessage(`Draft saved with ${warnings.length} issue(s): ${warnings.join('; ')}`, 'error')
    } else {
      showToastMessage('Draft saved.', 'success')
    }
  } catch (err) {
    messageType.value = 'error'
    message.value = err.message || 'Failed to save draft.'
  } finally {
    saving.value = ''
  }
}

async function publishDraft() {
  const payload = buildPublishAssignments()
  if (!Object.keys(payload).length) {
    showToastMessage('Nothing to publish -- there are no draft or changed shifts for this week.', 'error')
    return
  }

  saving.value = 'publish'
  message.value = ''
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.publish_weekly_draft', {
      department: department.value,
      week_start: isoDate(weekStart.value),
      assignments: payload,
    })
    const warnings = result?.warnings || []
    if (warnings.length) {
      showToastMessage(`Published with ${warnings.length} issue(s): ${warnings.join('; ')}`, 'error')
    } else {
      showToastMessage('Roster published.', 'success')
    }
    viewMode.value = 'roster'
    await loadRoster()
  } catch (err) {
    messageType.value = 'error'
    message.value = err.message || 'Failed to publish roster.'
  } finally {
    saving.value = ''
  }
}

watch(department, refreshData)
watch(weekStart, refreshData)

onMounted(async () => {
  await loadDepartments()
  await loadShiftTypeOptions()
  await refreshData()
})

// ---------------------------------------------------------------------------
// Derived stats
// ---------------------------------------------------------------------------

const totalSlots = computed(() => serverStats.value?.total_slots ?? staffList.value.length * days.value.length)
const assignedSlots = computed(() => serverStats.value?.assigned_slots ?? 0)
const coverageLevel = computed(() => serverStats.value?.coverage_level ?? 0)
const conflictAlerts = computed(() => serverStats.value?.conflict_alerts ?? 0)

const assignedSlotsBadgeLabel = computed(() => {
  if (previewMode.value) return 'Preview'
  if (viewMode.value === 'draft') return hasDraft.value ? 'Draft' : 'Default OFF'
  return 'Live'
})

const assignedSlotsBadgeClass = computed(() => {
  if (previewMode.value) return 'bg-amber-100 text-amber-600'
  if (viewMode.value === 'draft') return hasDraft.value ? 'bg-amber-100 text-amber-600' : 'bg-gray-100 text-gray-500'
  return 'bg-green-100 text-green-600'
})

const coverageLabel = computed(() => {
  if (coverageLevel.value >= 85) return 'Good'
  if (coverageLevel.value >= 60) return 'Watch'
  return 'Gap'
})

const coverageBadgeClass = computed(() => {
  if (coverageLevel.value >= 85) return 'bg-green-100 text-green-600'
  if (coverageLevel.value >= 60) return 'bg-amber-100 text-amber-600'
  return 'bg-red-100 text-red-600'
})

// ---------------------------------------------------------------------------
// Calendar event styling
// ---------------------------------------------------------------------------

function eventLabel(cell) {
  if (!cell) return 'OFF'
  if (cell.status === 'Off') return 'OFF'
  return cell.shift_type || 'Shift'
}

function eventColor(cell) {
  if (!cell) return 'ev-gray'
  if (cell.status === 'Off') return 'ev-gray'

  const lowered = (cell.shift_type || '').toLowerCase()
  if (lowered.includes('supervisor') || lowered.includes('lead')) return 'ev-green'
  if (lowered.includes('night')) return 'ev-purple'
  if (lowered.includes('afternoon') || lowered.includes('evening')) return 'ev-yellow'
  if (lowered.includes('morning')) return 'ev-blue'
  return 'ev-blue-light'
}

const LEGEND_ORDER = ['ev-blue', 'ev-yellow', 'ev-purple', 'ev-green', 'ev-blue-light', 'ev-gray', 'ev-offday']

const legendEntries = computed(() => {
  const labelsByColor = {}

  for (const staff of staffList.value) {
    for (const day of days.value) {
      const cell = staff.shifts[day.date]
      if (!cell) continue

      const color = eventColor(cell)
      const label = eventLabel(cell)

      if (!labelsByColor[color]) labelsByColor[color] = new Set()
      labelsByColor[color].add(label)
    }
  }

  // Always show Off even if not present in the current grid.
  if (!labelsByColor['ev-gray']) labelsByColor['ev-gray'] = new Set(['OFF'])

  return LEGEND_ORDER
    .filter((color) => labelsByColor[color])
    .map((color) => ({
      color,
      label: Array.from(labelsByColor[color]).sort().join(' / '),
    }))
})

// ---------------------------------------------------------------------------
// Draft editor: shift type options + cell styling
// ---------------------------------------------------------------------------

async function loadShiftTypeOptions() {
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.get_shift_types')
    if (result && result.length) {
      shiftTypeOptions.value = result
    }
  } catch (err) {
    // Keep fallback OFF/Leave options if Shift Types can't be loaded.
  }
}

function colorForShiftValue(value, cell) {
  if (value === 'OFF') return 'gray'

  const lowered = (value || '').toLowerCase()
  if (lowered.includes('supervisor') || lowered.includes('lead')) return 'green'
  if (lowered.includes('night')) return 'purple'
  if (lowered.includes('afternoon') || lowered.includes('evening')) return 'yellow'
  if (lowered.includes('morning')) return 'blue'
  return 'blue-light'
}

const SHIFT_CLASS_MAP = {
  blue: 'bg-blue-100 text-blue-700 border-blue-200',
  'blue-light': 'bg-sky-100 text-sky-700 border-sky-200',
  yellow: 'bg-amber-100 text-amber-700 border-amber-200',
  purple: 'bg-indigo-100 text-indigo-700 border-indigo-200',
  green: 'bg-cyan-100 text-cyan-700 border-cyan-200',
  gray: 'bg-gray-50 text-gray-500 border-gray-200',
  offday: 'bg-red-100 text-red-700 border-red-200',
}

const CHEVRON_CLASS_MAP = {
  blue: 'text-blue-500',
  'blue-light': 'text-sky-500',
  yellow: 'text-amber-500',
  purple: 'text-indigo-500',
  green: 'text-cyan-500',
  gray: 'text-gray-400',
  offday: 'text-red-500',
}

const SWATCH_CLASS_MAP = {
  blue: 'bg-blue-100',
  'blue-light': 'bg-sky-100',
  yellow: 'bg-amber-100',
  purple: 'bg-indigo-100',
  green: 'bg-cyan-100',
  gray: 'bg-gray-100 border border-gray-300',
  offday: 'bg-red-100',
}

function shiftClass(value, cell) {
  const base = SHIFT_CLASS_MAP[colorForShiftValue(value, cell)]
  if (cell?.draft) return `${base} ring-2 ring-amber-400 ring-offset-1`
  return base
}

function chevronClass(value, cell) {
  return CHEVRON_CLASS_MAP[colorForShiftValue(value, cell)]
}

function isLocked(cell) {
  // A cell is locked (read-only) if it represents an already-published
  // (submitted) Shift Assignment. Empty/OFF cells and unsaved drafts remain
  // editable.
  return Boolean(cell && !cell.draft && cell.value !== 'OFF')
}

const shiftLegend = computed(() => {
  const labelsByColor = {}

  for (const opt of shiftTypeOptions.value) {
    const color = colorForShiftValue(opt.value)
    if (!labelsByColor[color]) labelsByColor[color] = new Set()
    labelsByColor[color].add(opt.label)
  }

  return LEGEND_ORDER
    .map((entryColor) => entryColor.replace('ev-', ''))
    .filter((color) => labelsByColor[color])
    .map((color) => ({
      color,
      swatchClass: SWATCH_CLASS_MAP[color],
      label: Array.from(labelsByColor[color]).sort().join(' / '),
    }))
})

// ---------------------------------------------------------------------------
// AI Auto Assign (preview)
// ---------------------------------------------------------------------------

async function aiAutoAssign() {
  if (!department.value) return
  aiRunning.value = true
  message.value = ''
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.ai_auto_assign', {
      department: department.value,
      week_start: isoDate(weekStart.value),
    })
    if (result?.staff) {
      if (viewMode.value === 'draft') {
        staffList.value = result.staff.map((row) => {
          const shifts = {}
          for (const [date, cell] of Object.entries(row.shifts || {})) {
            shifts[date] = {
              value: cell.status === 'Off' ? 'OFF' : cell.status === 'Leave' ? 'Leave' : cell.shift_type,
              status: cell.status,
              time: cell.time,
              draft: true,
            }
          }
          return { ...mapDraftRow(row), shifts }
        })
      } else {
        staffList.value = result.staff.map(mapRosterRow)
      }
      serverStats.value = result.stats || serverStats.value
      previewMode.value = true
    }
    messageType.value = 'success'
    message.value = viewMode.value === 'draft'
      ? 'AI Auto Assign preview generated. Review below, then Save Draft or Publish.'
      : 'AI Auto Assign preview generated. Switch to Draft / Edit to save or publish it.'
  } catch (err) {
    messageType.value = 'error'
    message.value = err.message || 'AI Auto Assign failed.'
  } finally {
    aiRunning.value = false
  }
}

// ---------------------------------------------------------------------------
// Shift Assignment Tool modal
// ---------------------------------------------------------------------------

const showAssignmentTool = ref(false)
const toolOptions = ref({
  companies: [], shift_types: [], branches: [], designations: [],
  employment_types: [], grades: [], departments: [], default_company: '',
})
const toolForm = ref({
  action: 'Assign Shift',
  company: '',
  shift_type: '',
  status: 'Active',
  start_date: '',
  end_date: '',
  department: '',
  branch: '',
  designation: '',
  grade: '',
  employment_type: '',
})
const eligibleEmployees = ref([])
const selectedEmployees = ref([])
const loadingEmployees = ref(false)
const assigning = ref(false)
const toolMessage = ref('')
const toolMessageType = ref('success')
const employeeListMessage = ref('Set the filters above and click "Search Employees".')

async function loadAssignmentToolOptions() {
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.get_assignment_tool_options')
    toolOptions.value = result || toolOptions.value
  } catch (err) {
    // Non-fatal -- modal still usable with empty dropdowns.
  }
}

async function openAssignmentTool() {
  if (!toolOptions.value.companies.length) await loadAssignmentToolOptions()

  toolForm.value = {
    action: 'Assign Shift',
    company: toolOptions.value.default_company || '',
    shift_type: '',
    status: 'Active',
    start_date: isoDate(new Date()),
    end_date: '',
    department: department.value || '',
    branch: '',
    designation: '',
    grade: '',
    employment_type: '',
  }
  eligibleEmployees.value = []
  selectedEmployees.value = []
  toolMessage.value = ''
  employeeListMessage.value = 'Set the filters above and click "Search Employees".'
  showAssignmentTool.value = true
}

function closeAssignmentTool() {
  if (assigning.value) return
  showAssignmentTool.value = false
}

const canSearchEmployees = computed(() => Boolean(toolForm.value.start_date))

async function searchEmployees() {
  loadingEmployees.value = true
  toolMessage.value = ''
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.get_assignment_tool_employees', {
      company: toolForm.value.company,
      branch: toolForm.value.branch,
      department: toolForm.value.department,
      designation: toolForm.value.designation,
      grade: toolForm.value.grade,
      employment_type: toolForm.value.employment_type,
      shift_type: toolForm.value.shift_type,
      start_date: toolForm.value.start_date,
      end_date: toolForm.value.end_date,
      status: toolForm.value.status,
    })
    eligibleEmployees.value = result || []
    selectedEmployees.value = []
    employeeListMessage.value = eligibleEmployees.value.length
      ? ''
      : 'There are no employees without conflicting Shift Assignments based on the given filters.'
  } catch (err) {
    toolMessageType.value = 'error'
    toolMessage.value = err.message || 'Failed to search employees.'
  } finally {
    loadingEmployees.value = false
  }
}

const allSelected = computed(() =>
  eligibleEmployees.value.length > 0 && selectedEmployees.value.length === eligibleEmployees.value.length
)

function toggleSelectAll() {
  if (allSelected.value) {
    selectedEmployees.value = []
  } else {
    selectedEmployees.value = eligibleEmployees.value.map((e) => e.employee)
  }
}

const canAssign = computed(() =>
  Boolean(toolForm.value.company && toolForm.value.shift_type && toolForm.value.start_date && selectedEmployees.value.length)
)

async function assignShift() {
  if (!canAssign.value) return
  assigning.value = true
  toolMessage.value = ''
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.bulk_assign_shift', {
      employees: selectedEmployees.value,
      company: toolForm.value.company,
      shift_type: toolForm.value.shift_type,
      start_date: toolForm.value.start_date,
      end_date: toolForm.value.end_date,
      status: toolForm.value.status,
    })
    const successList = result?.success || []
    const failureList = result?.failure || []

    const names = successList.map((item) => {
      return item.employee_name || item.employee || item.name || item
    })

    await refreshData()
    let toastText
    if (names.length === 1) {
      toastText = `Shift assigned to ${names[0]}.`
    } else if (names.length > 1) {
      toastText = `Shift assigned to ${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}.`
    } else {
      toastText = 'No shifts were assigned.'
    }
    if (failureList.length) {
      // Surface the actual reason(s) rather than just a bare count -- this
      // is what was previously swallowed, leaving conflicts (e.g. "already
      // has an active Shift Assignment") invisible to the user.
      const reasons = failureList.map((f) => {
        const who = f.employee_name || f.employee || 'Unknown'
        return f.reason ? `${who}: ${f.reason}` : who
      })
      toastText += ` ${failureList.length} failed (${reasons.join('; ')}).`
    }

    showToastMessage(toastText, failureList.length && !names.length ? 'error' : 'success')

    showAssignmentTool.value = false
  } catch (err) {
    toolMessageType.value = 'error'
    toolMessage.value = err.message || 'Failed to assign shift.'
  } finally {
    assigning.value = false
  }
}

// ---------------------------------------------------------------------------
// Add Shift Type modal
// ---------------------------------------------------------------------------

const showAddShiftType = ref(false)
const shiftTypeForm = ref({ name: '', start_time: '', end_time: '' })
const creatingShiftType = ref(false)
const shiftTypeMessage = ref('')
const shiftTypeMessageType = ref('success')

function openAddShiftType() {
  shiftTypeForm.value = { name: '', start_time: '', end_time: '' }
  shiftTypeMessage.value = ''
  showAddShiftType.value = true
}

function closeAddShiftType() {
  if (creatingShiftType.value) return
  showAddShiftType.value = false
}

const canCreateShiftType = computed(() =>
  Boolean(shiftTypeForm.value.name.trim() && shiftTypeForm.value.start_time && shiftTypeForm.value.end_time)
)

async function createShiftType() {
  if (!canCreateShiftType.value) return
  creatingShiftType.value = true
  shiftTypeMessage.value = ''
  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.create_shift_type', {
      name: shiftTypeForm.value.name.trim(),
      start_time: shiftTypeForm.value.start_time,
      end_time: shiftTypeForm.value.end_time,
    })

    // Refresh dropdown options so the new Shift Type is immediately selectable.
    await loadAssignmentToolOptions()

    showToastMessage(`Shift Type "${result?.name || shiftTypeForm.value.name.trim()}" added.`, 'success')
    showAddShiftType.value = false
  } catch (err) {
    shiftTypeMessageType.value = 'error'
    shiftTypeMessage.value = err.message || 'Failed to add Shift Type.'
  } finally {
    creatingShiftType.value = false
  }
}

// ---------------------------------------------------------------------------
// View All Shift Types modal
// ---------------------------------------------------------------------------

const showViewShiftTypes = ref(false)
const allShiftTypes = ref([])
const loadingShiftTypeList = ref(false)

async function loadAllShiftTypes() {
  loadingShiftTypeList.value = true
  try {
    allShiftTypes.value = await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.get_all_shift_types') || []
  } catch (err) {
    showToastMessage(err.message || 'Failed to load Shift Types.', 'error')
    allShiftTypes.value = []
  } finally {
    loadingShiftTypeList.value = false
  }
}

async function openViewShiftTypes() {
  showViewShiftTypes.value = true
  await loadAllShiftTypes()
}

function closeViewShiftTypes() {
  showViewShiftTypes.value = false
}

// ---------------------------------------------------------------------------
// Edit Shift Type modal (opened from a row inside View All Shift Types)
// ---------------------------------------------------------------------------

const showEditShiftType = ref(false)
const editShiftTypeForm = ref({ name: '', start_time: '', end_time: '' })
const savingEditShiftType = ref(false)
const editShiftTypeMessage = ref('')
const editShiftTypeMessageType = ref('success')

function _toTimeInputValue(value) {
  // Shift Type stores time as "HH:MM:SS" (or a timedelta string) -- the
  // <input type="time"> element wants "HH:MM".
  const str = cstr(value || '')
  const parts = str.split(':')
  if (parts.length >= 2) return `${parts[0].padStart(2, '0')}:${parts[1].padStart(2, '0')}`
  return ''
}

function cstr(value) {
  return value === null || value === undefined ? '' : String(value)
}

function openEditShiftType(shiftType) {
  editShiftTypeForm.value = {
    name: shiftType.name,
    start_time: _toTimeInputValue(shiftType.start_time),
    end_time: _toTimeInputValue(shiftType.end_time),
  }
  editShiftTypeMessage.value = ''
  showEditShiftType.value = true
}

function closeEditShiftType() {
  if (savingEditShiftType.value) return
  showEditShiftType.value = false
}

const canSaveEditShiftType = computed(() =>
  Boolean(editShiftTypeForm.value.start_time && editShiftTypeForm.value.end_time)
)

async function saveEditShiftType() {
  if (!canSaveEditShiftType.value) return
  savingEditShiftType.value = true
  editShiftTypeMessage.value = ''
  try {
    await callMethod('rhohotel.rhocom_hotel.api.weekly_shift_generator.update_shift_type', {
      name: editShiftTypeForm.value.name,
      start_time: editShiftTypeForm.value.start_time,
      end_time: editShiftTypeForm.value.end_time,
    })

    // Refresh both the list modal (so the new time shows immediately) and
    // the dropdown options used across the draft editor / assignment tool.
    await loadAllShiftTypes()
    await loadShiftTypeOptions()
    await loadAssignmentToolOptions()

    showToastMessage(`Shift Type "${editShiftTypeForm.value.name}" updated.`, 'success')
    showEditShiftType.value = false
  } catch (err) {
    editShiftTypeMessageType.value = 'error'
    editShiftTypeMessage.value = err.message || 'Failed to update Shift Type.'
  } finally {
    savingEditShiftType.value = false
  }
}
</script>

<style scoped>
.cal-event { border-radius: 8px; padding: 8px 10px; min-height: 50px; }
.ev-blue       { background: #dbeafe; color: #1e3a8a; }
.ev-blue-light { background: #e0f2fe; color: #0c4a6e; }
.ev-purple     { background: #ede9fe; color: #4c1d95; }
.ev-yellow     { background: #fef9c3; color: #713f12; }
.ev-green      { background: #dcfce7; color: #14532d; }
.ev-gray       { background: #f1f5f9; color: #475569; }
.ev-offday     { background: #fef2f2; color: #991b1b; }
</style>