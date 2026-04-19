<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">

    <!-- Header Card -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Task Control</h2>
        <p class="text-xs text-gray-400 mt-0.5">Manage issue reporting, diagnosis, work execution, material usage, and technician completion from one task page.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/maintenance/list')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Save Draft</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">Complete Task</button>
      </div>
    </div>

    <!-- Body -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:20px;">

      <!-- Left -->
      <div class="space-y-4">

        <!-- Task Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Task Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Task ID</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold text-gray-900">MNT-000219</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Task Type</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                <option>Corrective Maintenance</option>
                <option>Preventive Maintenance</option>
                <option>Inspection</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Priority</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                <option>Urgent</option>
                <option>Due</option>
                <option>Normal</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Asset Details -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Asset Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Asset Tag</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">AST-003761</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Asset Name</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">Industrial Laundry Dryer</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Location</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">Laundry Room</div>
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Issue Reported</p>
            <textarea rows="3" placeholder="Describe fault, incident, or maintenance request details..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none"></textarea>
          </div>
        </div>

        <!-- Assignment Section -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Assignment Section</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Assigned Technician</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                <option>Engr. Paul</option>
                <option>Engr. Musa</option>
                <option>Tech Team A</option>
                <option>Tech Team B</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Supervisor</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                <option>Maintenance Supervisor</option>
              </select>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Start Time</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">18 Apr 2026 • 10:15 AM</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Expected Duration</p>
              <input type="text" placeholder="3 hrs" class="w-full px-3 py-2.5 text-xs border border-blue-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </div>

        <!-- Parts / Material Usage -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Parts / Material Usage</h3>
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Part / Material</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Qty</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Store Impact</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Notes</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr>
                <td class="py-2.5 pr-3"><input type="text" value="Motor coupling" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" /></td>
                <td class="py-2.5 pr-3"><input type="number" value="1" class="w-16 px-2 py-1.5 text-xs border border-gray-200 rounded text-center" /></td>
                <td class="py-2.5 pr-3"><button class="px-3 py-1.5 text-xs font-medium text-green-600 bg-green-50 rounded-lg">Reduce stock</button></td>
                <td class="py-2.5"><input type="text" value="Replacement" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" /></td>
              </tr>
              <tr>
                <td class="py-2.5 pr-3"><input type="text" value="Lubricant kit" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" /></td>
                <td class="py-2.5 pr-3"><input type="number" value="1" class="w-16 px-2 py-1.5 text-xs border border-gray-200 rounded text-center" /></td>
                <td class="py-2.5 pr-3"><button class="px-3 py-1.5 text-xs font-medium text-green-600 bg-green-50 rounded-lg">Reduce stock</button></td>
                <td class="py-2.5"><input type="text" value="Servicing" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" /></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Maintenance Checklist -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Maintenance Checklist</h3>
          <div class="flex items-center gap-6">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked class="w-4 h-4 accent-green-500" />
              <span class="text-xs text-gray-700">Fault diagnosed</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked class="w-4 h-4 accent-green-500" />
              <span class="text-xs text-gray-700">Parts replaced</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" class="w-4 h-4 accent-green-500" />
              <span class="text-xs text-gray-700">Test run passed</span>
            </label>
          </div>
        </div>
      </div>

      <!-- Right: Status Update -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Status Update Section</h3>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Current Task Status</p>
            <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
              <option>In Progress</option>
              <option>Open</option>
              <option>Completed</option>
              <option>On Hold</option>
            </select>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Final Asset Status</p>
            <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
              <option>Operational</option>
              <option>Under Repair</option>
              <option>Decommissioned</option>
            </select>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Inspection Required</p>
            <label class="flex items-center gap-2 cursor-pointer bg-gray-50 rounded-lg px-3 py-2.5 border border-gray-200">
              <input type="checkbox" checked class="w-4 h-4 accent-green-500" />
              <span class="text-xs text-gray-700">Yes, supervisor must verify repair</span>
            </label>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Completion Notes</p>
            <textarea rows="4" placeholder="Enter diagnosis, repair action taken, testing result, or follow-up recommendation..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none"></textarea>
          </div>
          <div class="mb-4">
            <p class="text-xs text-gray-500 mb-1.5">Photo / Proof</p>
            <button class="w-full py-2.5 text-xs font-medium text-blue-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50">
              Upload service photo
            </button>
          </div>
        </div>

        <!-- Quick Summary -->
        <div class="bg-blue-50 rounded-xl border border-blue-100 p-4">
          <h4 class="text-xs font-bold text-blue-700 mb-2">Laundry Dryer Task</h4>
          <p class="text-xs text-blue-600">Type: Corrective</p>
          <p class="text-xs text-blue-600 mt-0.5">Technician: Engr. Paul</p>
          <p class="text-xs text-blue-600 mt-0.5">Final status: Operational</p>
        </div>

        <!-- Related Actions -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <p class="text-xs font-semibold text-gray-700 mb-2">Related Actions</p>
          <button class="w-full py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">Request Part</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>