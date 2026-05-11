<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">
        <span class="cursor-pointer hover:text-blue-600" @click="$router.push('/assets-mgmt')">Assets</span>
        • <span class="cursor-pointer hover:text-blue-600" @click="$router.push('/assets-mgmt/repair')">Asset Repair</span>
        • {{ repair?.name || 'Loading...' }}
      </p>
    </div>

    <!-- Alerts (top) -->
    <div v-if="successMessage" class="bg-green-50 border border-green-200 rounded-xl px-6 py-4 flex items-start gap-2">
      <svg class="w-4 h-4 text-green-500 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
      <p class="text-xs text-green-800 font-medium">{{ successMessage }}</p>
    </div>
    <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-xl px-6 py-4 flex items-start gap-2">
      <svg class="w-4 h-4 text-red-500 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
      <p class="text-xs text-red-800 font-medium">{{ errorMessage }}</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 px-6 py-12 text-center">
      <p class="text-xs text-gray-400">Loading repair details...</p>
    </div>

    <template v-else-if="repair">
      <!-- Header -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <div class="flex items-center gap-3">
            <h3 class="text-sm font-bold text-gray-900">{{ repair.name }}</h3>
            <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass">{{ statusLabel }}</span>
            <span v-if="repair.rh_approved && repair.rh_approved !== 'Pending'"
              class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="approvalBadgeClass">
              {{ repair.rh_approved }}
            </span>
          </div>
          <p class="text-xs text-gray-400 mt-0.5">{{ repair.asset_name }} ({{ repair.asset }})</p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="$router.push('/assets-mgmt/repair')"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Back to List</button>

          <!-- Edit button -->
          <template v-if="canEdit && !editing">
            <button @click="startEditing"
              class="px-4 py-2 text-xs font-semibold text-white bg-gray-700 rounded-lg hover:bg-gray-800 transition-colors">
              Edit
            </button>
          </template>

          <!-- Save/Cancel editing -->
          <template v-if="editing">
            <button @click="cancelEditing"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel Edit</button>
            <button @click="saveEdit" :disabled="savingEdit"
              class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">
              {{ savingEdit ? 'Saving...' : 'Save Changes' }}
            </button>
          </template>

          <!-- Approve/Reject -->
          <template v-if="!editing && repair.rh_approved === 'Pending' && repair.docstatus === 0">
            <button @click="approveRepair"
              class="px-4 py-2 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">
              Approve
            </button>
            <button @click="showRejectModal = true"
              class="px-4 py-2 text-xs font-semibold text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors">
              Reject
            </button>
          </template>

          <!-- Complete -->
          <template v-if="!editing && repair.rh_approved === 'Approved' && repair.repair_status !== 'Completed'">
            <button @click="showCompleteModal = true"
              class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
              Mark Completed
            </button>
          </template>
        </div>
      </div>

      <!-- ============= VIEW MODE ============= -->
      <template v-if="!editing">

        <!-- Asset Info + Repair Details / Hotel Details -->
        <div class="grid grid-cols-2 gap-5">
          <!-- Left: Repair Details -->
          <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Repair Details</h4>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Asset</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.asset_name }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Asset ID</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.asset }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Company</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.company || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Failure Date</span>
                <span class="text-xs font-medium text-gray-900">{{ formatDate(repair.failure_date) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Repair Status</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.repair_status || 'Pending' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Completion Date</span>
                <span class="text-xs font-medium text-gray-900">{{ formatDate(repair.completion_date) || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Downtime</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.downtime || '—' }}</span>
              </div>
            </div>
          </div>

          <!-- Right: Hotel Details -->
          <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Hotel Details</h4>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Location Type</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.rh_location_type || '—' }}</span>
              </div>
              <div v-if="repair.rh_location_type === 'Room'" class="flex justify-between">
                <span class="text-xs text-gray-500">Hotel Room</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.rh_hotel_room_number || repair.rh_hotel_room || '—' }}</span>
              </div>
              <div v-if="repair.rh_location_type === 'Asset Location'" class="flex justify-between">
                <span class="text-xs text-gray-500">Asset Location</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.rh_asset_location || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Reported By</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.rh_reported_by_name || repair.rh_reported_by || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Priority</span>
                <span class="text-xs font-medium" :class="priorityClass(repair.rh_priority)">{{ repair.rh_priority || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Issue Type</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.rh_issue_type || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Assigned Technician</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.rh_technician_name || repair.rh_assigned_technician || '—' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Accounting Dimensions -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Accounting Dimensions</h4>
          <div class="grid grid-cols-2 gap-6">
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Cost Center</span>
              <span class="text-xs font-medium text-gray-900">{{ repair.cost_center || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Project</span>
              <span class="text-xs font-medium text-gray-900">{{ repair.project || '—' }}</span>
            </div>
          </div>
        </div>

        <!-- Accounting Details -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Accounting Details</h4>
          <div class="grid grid-cols-2 gap-6">
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Purchase Invoice</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.purchase_invoice || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Capitalize Repair Cost</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.capitalize_repair_cost ? 'Yes' : 'No' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Stock Consumed During Repair</span>
                <span class="text-xs font-medium text-gray-900">{{ repair.stock_consumption ? 'Yes' : 'No' }}</span>
              </div>
            </div>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Repair Cost</span>
                <span class="text-xs font-medium text-gray-900">{{ formatCurrency(repair.repair_cost) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Stock Consumption Details (conditional: when stock_consumption is checked) -->
        <div v-if="repair.stock_consumption" class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h4 class="text-xs font-bold text-gray-900 uppercase tracking-wider">Stock Consumption Details</h4>
          </div>
          <table v-if="repair.stock_items && repair.stock_items.length" class="w-full">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50">
                <th class="text-left text-xs font-medium text-gray-500 px-6 py-3">Item</th>
                <th class="text-left text-xs font-medium text-gray-500 px-4 py-3">Warehouse</th>
                <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Valuation Rate</th>
                <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Consumed Qty</th>
                <th class="text-right text-xs font-medium text-gray-500 px-4 py-3">Total Value</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in repair.stock_items" :key="idx" class="border-b border-gray-50">
                <td class="px-6 py-3 text-xs text-gray-900">{{ item.item_name || item.item_code }}</td>
                <td class="px-4 py-3 text-xs text-gray-600">{{ item.warehouse || '—' }}</td>
                <td class="px-4 py-3 text-xs text-gray-600 text-right">{{ formatCurrency(item.valuation_rate) }}</td>
                <td class="px-4 py-3 text-xs text-gray-600 text-right">{{ item.consumed_quantity }}</td>
                <td class="px-4 py-3 text-xs text-gray-600 text-right">{{ formatCurrency(item.total_value) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="px-6 py-4 text-xs text-gray-400">No stock items consumed.</div>
          <div v-if="repair.total_repair_cost" class="px-6 py-3 border-t border-gray-100 flex justify-between">
            <span class="text-xs font-semibold text-gray-700">Total Repair Cost</span>
            <span class="text-xs font-bold text-gray-900">{{ formatCurrency(repair.total_repair_cost) }}</span>
          </div>
        </div>

        <!-- Asset Depreciation Details (conditional: when capitalize_repair_cost is checked) -->
        <div v-if="repair.capitalize_repair_cost" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Asset Depreciation Details</h4>
          <div class="flex justify-between">
            <span class="text-xs text-gray-500">Increase in Asset Life (Months)</span>
            <span class="text-xs font-medium text-gray-900">{{ repair.increase_in_asset_life || '—' }}</span>
          </div>
        </div>

        <!-- Approval Details -->
        <div v-if="repair.rh_approved !== 'Pending'" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Approval Details</h4>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <span class="text-xs text-gray-500">Status</span>
              <p class="text-xs font-semibold mt-1" :class="repair.rh_approved === 'Approved' ? 'text-green-600' : 'text-red-500'">{{ repair.rh_approved }}</p>
            </div>
            <div>
              <span class="text-xs text-gray-500">Approved By</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ repair.rh_approved_by_name || repair.rh_approved_by || '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-gray-500">Approved On</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(repair.rh_approved_on) || '—' }}</p>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h4 class="text-xs font-bold text-gray-900 mb-3 uppercase tracking-wider">Description</h4>
          <div class="grid grid-cols-2 gap-6">
            <div>
              <span class="text-xs text-gray-500 block mb-1">Error Description</span>
              <p class="text-xs text-gray-700 leading-relaxed whitespace-pre-wrap">{{ repair.description || 'No description provided.' }}</p>
            </div>
            <div>
              <span class="text-xs text-gray-500 block mb-1">Actions Performed</span>
              <p class="text-xs text-gray-700 leading-relaxed whitespace-pre-wrap">{{ repair.actions_performed || '—' }}</p>
            </div>
          </div>
        </div>

        <!-- Meta -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <div class="grid grid-cols-3 gap-4">
            <div>
              <span class="text-xs text-gray-500">Created By</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ repair.created_by }}</p>
            </div>
            <div>
              <span class="text-xs text-gray-500">Created On</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(repair.creation) }}</p>
            </div>
            <div>
              <span class="text-xs text-gray-500">Last Modified</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(repair.modified) }}</p>
            </div>
          </div>
        </div>
      </template>

      <!-- ============= EDIT MODE ============= -->
      <template v-if="editing">

        <!-- Section: Asset & Repair Details -->
        <div class="bg-white rounded-xl border border-blue-200 px-6 py-6">
          <h4 class="text-xs font-bold text-blue-700 mb-4 uppercase tracking-wider">Asset & Repair Details</h4>
          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Asset <span class="text-red-500">*</span></label>
              <select v-model="editForm.asset"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select an asset...</option>
                <option v-for="a in assetsList" :key="a.name" :value="a.name">{{ a.asset_name }} ({{ a.name }})</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Failure Date <span class="text-red-500">*</span></label>
              <input v-model="editForm.failure_date" type="datetime-local"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Repair Status</label>
              <select v-model="editForm.repair_status"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50" disabled>
                <option>Pending</option>
                <option>Completed</option>
                <option>Cancelled</option>
              </select>
              <p class="text-xs text-gray-400 mt-1">Status changes through Approve/Reject/Complete actions.</p>
            </div>
          </div>
        </div>

        <!-- Section: Hotel Details -->
        <div class="bg-white rounded-xl border border-blue-200 px-6 py-6">
          <h4 class="text-xs font-bold text-blue-700 mb-4 uppercase tracking-wider">Hotel Details</h4>
          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Location Type</label>
              <select v-model="editForm.rh_location_type"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="Room">Room</option>
                <option value="Asset Location">Asset Location</option>
              </select>
            </div>
            <div v-if="editForm.rh_location_type === 'Room'">
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Hotel Room</label>
              <select v-model="editForm.rh_hotel_room"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select room...</option>
                <option v-for="r in hotelRoomsList" :key="r.name" :value="r.name">{{ r.room_number }} ({{ r.name }})</option>
              </select>
            </div>
            <div v-if="editForm.rh_location_type === 'Asset Location'">
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Asset Location</label>
              <select v-model="editForm.rh_asset_location"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select location...</option>
                <option v-for="l in locationsList" :key="l.name" :value="l.name">{{ l.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Reported By <span class="text-red-500">*</span></label>
              <select v-model="editForm.rh_reported_by"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select employee...</option>
                <option v-for="e in employeesList" :key="e.name" :value="e.name">{{ e.employee_name }} ({{ e.name }})</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Priority</label>
              <select v-model="editForm.rh_priority"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Issue Type</label>
              <select v-model="editForm.rh_issue_type"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select issue type...</option>
                <option>Plumbing</option><option>Electrical</option><option>HVAC</option>
                <option>Furniture</option><option>Appliance</option><option>Electronics</option>
                <option>Structural</option><option>Other</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Assigned Technician</label>
              <select v-model="editForm.rh_assigned_technician"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select technician...</option>
                <option v-for="t in techniciansList" :key="t.name" :value="t.name">{{ t.technician_name }} ({{ t.name }})</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Section: Accounting Dimensions -->
        <div class="bg-white rounded-xl border border-blue-200 px-6 py-6">
          <h4 class="text-xs font-bold text-blue-700 mb-4 uppercase tracking-wider">Accounting Dimensions</h4>
          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Cost Center</label>
              <select v-model="editForm.cost_center"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select cost center...</option>
                <option v-for="cc in costCentersList" :key="cc.name" :value="cc.name">{{ cc.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Project</label>
              <select v-model="editForm.project"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select project...</option>
                <option v-for="p in projectsList" :key="p.name" :value="p.name">{{ p.project_name || p.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Section: Accounting Details -->
        <div class="bg-white rounded-xl border border-blue-200 px-6 py-6">
          <h4 class="text-xs font-bold text-blue-700 mb-4 uppercase tracking-wider">Accounting Details</h4>
          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Purchase Invoice</label>
              <input v-model="editForm.purchase_invoice" type="text" placeholder="e.g. ACC-PINV-2024-00001"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Repair Cost</label>
              <input v-model.number="editForm.repair_cost" type="number" min="0" step="0.01"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div class="flex items-center gap-2">
              <input v-model="editForm.capitalize_repair_cost" type="checkbox" id="edit_capitalize"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500" />
              <label for="edit_capitalize" class="text-xs text-gray-700">Capitalize Repair Cost</label>
            </div>
            <div class="flex items-center gap-2">
              <input v-model="editForm.stock_consumption" type="checkbox" id="edit_stock"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500" />
              <label for="edit_stock" class="text-xs text-gray-700">Stock Consumed During Repair</label>
            </div>
          </div>
        </div>

        <!-- Section: Stock Consumption Details (conditional) -->
        <div v-if="editForm.stock_consumption" class="bg-white rounded-xl border border-blue-200 px-6 py-6">
          <h4 class="text-xs font-bold text-blue-700 mb-4 uppercase tracking-wider">Stock Consumption Details</h4>
          <table class="w-full mb-4">
            <thead>
              <tr class="border-b border-gray-200">
                <th class="text-left text-xs font-medium text-gray-500 pb-2 pr-2">Item <span class="text-red-500">*</span></th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2 pr-2">Warehouse <span class="text-red-500">*</span></th>
                <th class="text-right text-xs font-medium text-gray-500 pb-2 pr-2">Consumed Qty</th>
                <th class="w-10"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in editForm.stock_items" :key="idx" class="border-b border-gray-50">
                <td class="py-2 pr-2">
                  <select v-model="row.item_code"
                    class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">Select item...</option>
                    <option v-for="it in itemsList" :key="it.name" :value="it.name">{{ it.item_name || it.name }}</option>
                  </select>
                </td>
                <td class="py-2 pr-2">
                  <select v-model="row.warehouse"
                    class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">Select warehouse...</option>
                    <option v-for="w in warehousesList" :key="w.name" :value="w.name">{{ w.name }}</option>
                  </select>
                </td>
                <td class="py-2 pr-2">
                  <input v-model.number="row.consumed_quantity" type="number" min="0" step="1"
                    class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-lg text-right focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </td>
                <td class="py-2 text-center">
                  <button @click="removeStockRow(idx)" class="text-red-400 hover:text-red-600">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <button @click="addStockRow"
            class="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors">
            + Add Row
          </button>
        </div>

        <!-- Section: Asset Depreciation Details (conditional) -->
        <div v-if="editForm.capitalize_repair_cost" class="bg-white rounded-xl border border-blue-200 px-6 py-6">
          <h4 class="text-xs font-bold text-blue-700 mb-4 uppercase tracking-wider">Asset Depreciation Details</h4>
          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Increase in Asset Life (Months)</label>
              <input v-model.number="editForm.increase_in_asset_life" type="number" min="0"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </div>

        <!-- Section: Description -->
        <div class="bg-white rounded-xl border border-blue-200 px-6 py-6">
          <h4 class="text-xs font-bold text-blue-700 mb-4 uppercase tracking-wider">Description</h4>
          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Error Description</label>
              <textarea v-model="editForm.description" rows="4"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5">Actions Performed</label>
              <textarea v-model="editForm.actions_performed" rows="4"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
            </div>
          </div>
        </div>
      </template>
    </template>

    <!-- Reject Modal -->
    <div v-if="showRejectModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showRejectModal = false">
      <div class="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h4 class="text-sm font-bold text-gray-900 mb-3">Reject Asset Repair</h4>
        <p class="text-xs text-gray-500 mb-4">Provide a reason for rejecting this repair request.</p>
        <textarea v-model="rejectReason" rows="3" placeholder="Reason for rejection..."
          class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 mb-4"></textarea>
        <div class="flex justify-end gap-2">
          <button @click="showRejectModal = false"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
          <button @click="rejectRepair"
            class="px-4 py-2 text-xs font-semibold text-white bg-red-600 rounded-lg hover:bg-red-700">Confirm Reject</button>
        </div>
      </div>
    </div>

    <!-- Complete Modal -->
    <div v-if="showCompleteModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showCompleteModal = false">
      <div class="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h4 class="text-sm font-bold text-gray-900 mb-3">Mark Repair as Completed</h4>
        <div class="space-y-3 mb-4">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Completion Date</label>
            <input v-model="completeForm.completion_date" type="datetime-local"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Actions Performed</label>
            <textarea v-model="completeForm.actions_performed" rows="3" placeholder="Describe what was done..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2">
          <button @click="showCompleteModal = false"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
          <button @click="completeRepair"
            class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Mark Completed</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const repair = ref(null)
const editing = ref(false)
const savingEdit = ref(false)
const showRejectModal = ref(false)
const showCompleteModal = ref(false)
const rejectReason = ref('')
const successMessage = ref('')
const errorMessage = ref('')

function stripHtml(str) {
  if (!str) return str
  return str.replace(/<[^>]*>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').trim()
}

// Dropdown data for edit mode
const assetsList = ref([])
const employeesList = ref([])
const techniciansList = ref([])
const hotelRoomsList = ref([])
const costCentersList = ref([])
const projectsList = ref([])
const locationsList = ref([])
const itemsList = ref([])
const warehousesList = ref([])

const editForm = reactive({
  asset: '',
  failure_date: '',
  repair_status: 'Pending',
  description: '',
  actions_performed: '',
  repair_cost: 0,
  capitalize_repair_cost: false,
  stock_consumption: false,
  stock_items: [],
  increase_in_asset_life: 0,
  cost_center: '',
  project: '',
  purchase_invoice: '',
  rh_reported_by: '',
  rh_priority: 'Medium',
  rh_issue_type: '',
  rh_assigned_technician: '',
  rh_location_type: 'Room',
  rh_hotel_room: '',
  rh_asset_location: '',
})

const completeForm = reactive({
  completion_date: '',
  actions_performed: '',
})

// Can edit: draft, not completed, not rejected
const canEdit = computed(() => {
  if (!repair.value) return false
  return repair.value.docstatus === 0
    && repair.value.repair_status !== 'Completed'
    && repair.value.rh_approved !== 'Rejected'
})

const statusLabel = computed(() => {
  if (!repair.value) return ''
  const r = repair.value
  if (r.rh_approved === 'Rejected' || r.repair_status === 'Cancelled') return 'Rejected'
  if (r.repair_status === 'Completed') return 'Completed'
  if (r.rh_approved === 'Approved') return 'Approved'
  return 'Pending'
})

const statusClass = computed(() => {
  return {
    'Pending':   'bg-yellow-50 text-yellow-600',
    'Approved':  'bg-green-50 text-green-600',
    'Completed': 'bg-blue-50 text-blue-600',
    'Rejected':  'bg-red-50 text-red-500',
  }[statusLabel.value] || 'bg-gray-100 text-gray-500'
})

const approvalBadgeClass = computed(() => {
  if (!repair.value) return ''
  return {
    'Approved': 'bg-green-100 text-green-700',
    'Rejected': 'bg-red-100 text-red-600',
  }[repair.value.rh_approved] || ''
})

function priorityClass(p) {
  return {
    'Critical': 'text-red-600 font-bold',
    'High':     'text-orange-600 font-semibold',
    'Medium':   'text-yellow-600',
    'Low':      'text-gray-600',
  }[p] || 'text-gray-900'
}

function formatDateForInput(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// Stock items helpers
function addStockRow() {
  editForm.stock_items.push({ item_code: '', warehouse: '', consumed_quantity: 1 })
}

function removeStockRow(idx) {
  editForm.stock_items.splice(idx, 1)
}

function startEditing() {
  const r = repair.value
  editForm.asset = r.asset || ''
  editForm.failure_date = formatDateForInput(r.failure_date)
  editForm.repair_status = r.repair_status || 'Pending'
  editForm.description = r.description || ''
  editForm.actions_performed = r.actions_performed || ''
  editForm.repair_cost = r.repair_cost || 0
  editForm.capitalize_repair_cost = !!r.capitalize_repair_cost
  editForm.stock_consumption = !!r.stock_consumption
  editForm.increase_in_asset_life = r.increase_in_asset_life || 0
  editForm.cost_center = r.cost_center || ''
  editForm.project = r.project || ''
  editForm.purchase_invoice = r.purchase_invoice || ''
  editForm.rh_reported_by = r.rh_reported_by || ''
  editForm.rh_priority = r.rh_priority || 'Medium'
  editForm.rh_issue_type = r.rh_issue_type || ''
  editForm.rh_assigned_technician = r.rh_assigned_technician || ''
  editForm.rh_location_type = r.rh_location_type || 'Room'
  editForm.rh_hotel_room = r.rh_hotel_room || ''
  editForm.rh_asset_location = r.rh_asset_location || ''

  // Copy stock items
  editForm.stock_items = (r.stock_items || []).map(item => ({
    item_code: item.item_code || '',
    warehouse: item.warehouse || '',
    consumed_quantity: item.consumed_quantity || 1,
  }))

  loadDropdowns()
  editing.value = true
}

function cancelEditing() {
  editing.value = false
}

function loadDropdowns() {
  const company = repair.value?.company || ''
  const companyParams = company ? { company } : {}
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_assets_for_repair', auto: true, onSuccess(d) { assetsList.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_employees_for_repair', auto: true, onSuccess(d) { employeesList.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_technicians_for_repair', auto: true, onSuccess(d) { techniciansList.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_hotel_rooms_for_repair', auto: true, onSuccess(d) { hotelRoomsList.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_cost_centers', params: companyParams, auto: true, onSuccess(d) { costCentersList.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_projects', params: companyParams, auto: true, onSuccess(d) { projectsList.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_locations', auto: true, onSuccess(d) { locationsList.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_items_for_stock', params: companyParams, auto: true, onSuccess(d) { itemsList.value = d } })
  createResource({ url: 'rhohotel.rhocom_hotel.api.asset_repair.get_warehouses', params: companyParams, auto: true, onSuccess(d) { warehousesList.value = d } })
}

function saveEdit() {
  savingEdit.value = true
  successMessage.value = ''
  errorMessage.value = ''

  const params = {
    repair_name: repair.value.name,
    asset: editForm.asset,
    failure_date: editForm.failure_date,
    description: editForm.description,
    actions_performed: editForm.actions_performed,
    repair_cost: editForm.repair_cost || 0,
    capitalize_repair_cost: editForm.capitalize_repair_cost ? 1 : 0,
    stock_consumption: editForm.stock_consumption ? 1 : 0,
    increase_in_asset_life: editForm.capitalize_repair_cost ? (editForm.increase_in_asset_life || 0) : 0,
    cost_center: editForm.cost_center || null,
    project: editForm.project || null,
    purchase_invoice: editForm.purchase_invoice || null,
    rh_reported_by: editForm.rh_reported_by || null,
    rh_priority: editForm.rh_priority || null,
    rh_issue_type: editForm.rh_issue_type || null,
    rh_assigned_technician: editForm.rh_assigned_technician || null,
    rh_location_type: editForm.rh_location_type || null,
    rh_hotel_room: editForm.rh_location_type === 'Room' ? (editForm.rh_hotel_room || null) : null,
    rh_asset_location: editForm.rh_location_type === 'Asset Location' ? (editForm.rh_asset_location || null) : null,
  }

  // Include stock_items if stock consumption is enabled
  if (editForm.stock_consumption) {
    params.stock_items = JSON.stringify(editForm.stock_items.filter(r => r.item_code))
  } else {
    params.stock_items = JSON.stringify([])
  }

  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_repair.update_asset_repair',
    params,
    onSuccess(data) {
      savingEdit.value = false
      editing.value = false
      successMessage.value = data.message
      fetchRepair()
    },
    onError(err) {
      savingEdit.value = false
      errorMessage.value = stripHtml(err?.messages?.[0] || err?.message || 'Failed to update.')
    }
  })
  resource.fetch()
}

function fetchRepair() {
  loading.value = true
  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_repair.get_asset_repair',
    params: { repair_name: route.params.id },
    onSuccess(data) {
      repair.value = data
      loading.value = false
    },
    onError(err) {
      loading.value = false
      errorMessage.value = stripHtml(err?.messages?.[0] || 'Failed to load repair details.')
    }
  })
  resource.fetch()
}

function approveRepair() {
  successMessage.value = ''
  errorMessage.value = ''
  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_repair.approve_asset_repair',
    params: { repair_name: repair.value.name },
    onSuccess(data) {
      successMessage.value = data.message
      fetchRepair()
    },
    onError(err) {
      errorMessage.value = stripHtml(err?.messages?.[0] || err?.message || 'Failed to approve.')
    }
  })
  resource.fetch()
}

function rejectRepair() {
  successMessage.value = ''
  errorMessage.value = ''
  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_repair.reject_asset_repair',
    params: { repair_name: repair.value.name, reason: rejectReason.value },
    onSuccess(data) {
      successMessage.value = data.message
      showRejectModal.value = false
      rejectReason.value = ''
      fetchRepair()
    },
    onError(err) {
      errorMessage.value = stripHtml(err?.messages?.[0] || err?.message || 'Failed to reject.')
    }
  })
  resource.fetch()
}

function completeRepair() {
  successMessage.value = ''
  errorMessage.value = ''
  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.asset_repair.complete_asset_repair',
    params: {
      repair_name: repair.value.name,
      completion_date: completeForm.completion_date || null,
      actions_performed: completeForm.actions_performed || null,
    },
    onSuccess(data) {
      successMessage.value = data.message
      showCompleteModal.value = false
      fetchRepair()
    },
    onError(err) {
      errorMessage.value = stripHtml(err?.messages?.[0] || err?.message || 'Failed to complete.')
    }
  })
  resource.fetch()
}

function formatDate(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatCurrency(val) {
  if (!val && val !== 0) return '—'
  return new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', minimumFractionDigits: 0 }).format(val)
}

onMounted(() => {
  fetchRepair()
})
</script>
