<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Task Setup Control</h2>
        <p class="text-xs text-gray-400 mt-0.5">Create corrective or preventive work, assign technicians, and prepare the task for execution and follow-up.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/maintenance/list')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Save Draft</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">Create Task</button>
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
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400 italic">Auto generated on save</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Task Type</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select task type</option>
                <option>Corrective Maintenance</option>
                <option>Preventive Maintenance</option>
                <option>Inspection</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Priority</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select priority</option>
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
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select asset</option>
                <option>AST-003761</option>
                <option>AST-003762</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Asset Name</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400 italic">Auto-fill from asset</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Location</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400 italic">Auto-fill location</div>
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Issue Reported</p>
            <textarea rows="3" placeholder="Describe fault, maintenance need, symptoms, or inspection reason..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none"></textarea>
          </div>
        </div>

        <!-- Assignment Section -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Assignment Section</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Assigned Technician</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select technician</option>
                <option>Engr. Paul</option>
                <option>Engr. Musa</option>
                <option>Tech Team A</option>
                <option>Tech Team B</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Supervisor</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select supervisor</option>
                <option>Maintenance Supervisor</option>
              </select>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Planned Start</p>
              <input type="text" placeholder="Select date and time" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Expected Duration</p>
              <input type="text" placeholder="Enter expected duration" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
          </div>
        </div>

        <!-- Parts / Material Planning -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Parts / Material Planning</h3>
          <table class="w-full mb-3">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Part / Material</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Qty</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Store Impact</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="py-2 pr-3"><input type="text" placeholder="Add material or spare part" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" /></td>
                <td class="py-2 pr-3"><input type="number" value="0" class="w-16 px-2 py-1.5 text-xs border border-gray-200 rounded text-center" /></td>
                <td class="py-2 pr-3">
                  <select class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded text-gray-600">
                    <option value="">Select action</option>
                    <option>Reduce stock</option>
                    <option>No impact</option>
                  </select>
                </td>
                <td class="py-2"><input type="text" placeholder="Optional note" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" /></td>
              </tr>
            </tbody>
          </table>
          <button class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">+ Add Row</button>
        </div>

        <!-- Maintenance Checklist Template -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Maintenance Checklist Template</h3>
          <div class="flex items-center gap-6">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" class="w-4 h-4 accent-blue-500" />
              <span class="text-xs text-gray-700">Diagnosis required</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" class="w-4 h-4 accent-blue-500" />
              <span class="text-xs text-gray-700">Parts likely needed</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" class="w-4 h-4 accent-blue-500" />
              <span class="text-xs text-gray-700">Test run on completion</span>
            </label>
          </div>
        </div>
      </div>

      <!-- Right: Status Setup -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Status Setup Section</h3>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Initial Task Status</p>
            <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
              <option>Open</option>
              <option>In Progress</option>
              <option>Scheduled</option>
            </select>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Expected Asset Status After Repair</p>
            <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
              <option>Operational</option>
              <option>Under Repair</option>
            </select>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Inspection Required</p>
            <label class="flex items-center gap-2 cursor-pointer bg-gray-50 rounded-lg px-3 py-2.5 border border-gray-200">
              <input type="checkbox" checked class="w-4 h-4 accent-green-500" />
              <span class="text-xs text-gray-700">Require supervisor verification on completion</span>
            </label>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Preparation Notes</p>
            <textarea rows="4" placeholder="Add instructions, escalation note, or safety warning for technician..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none"></textarea>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Attachment / Reference</p>
            <button class="w-full py-2.5 text-xs font-medium text-blue-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50">Upload issue photo</button>
          </div>
        </div>

        <!-- Quick Summary -->
        <div class="bg-blue-50 rounded-xl border border-blue-100 p-4">
          <h4 class="text-xs font-bold text-blue-700 mb-2">New Task Preview</h4>
          <p class="text-xs text-blue-600">Task type: Not selected</p>
          <p class="text-xs text-blue-600 mt-0.5">Asset: Not selected</p>
          <p class="text-xs text-blue-600 mt-0.5">Status: Open</p>
        </div>

        <!-- Related Actions -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <p class="text-xs font-semibold text-gray-700 mb-2">Related Actions</p>
          <button class="w-full py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">Reserve Part</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>