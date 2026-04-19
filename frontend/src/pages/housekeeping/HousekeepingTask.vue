<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Task Control</h2>
        <p class="text-xs text-gray-400 mt-0.5">Track room servicing task, assign staff, confirm replenishment, and update final room readiness.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/housekeeping')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Save</button>
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
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Task ID</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold text-gray-900">HKT-2026-00084</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Task Type</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                <option>Checkout Cleaning</option>
                <option>Daily Cleaning</option>
                <option>Inspection Review</option>
                <option>Linen Refill</option>
                <option>Guest Request</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Priority</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                <option>High</option>
                <option>Urgent</option>
                <option>Medium</option>
                <option>Low</option>
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
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold text-gray-900">305</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">Executive Suite</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Floor</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">3</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Occupancy</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">Checked Out</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Last Guest</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">Sarah Johnson</div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Required By</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">18 Apr 2026 • 02:30 PM</div>
            </div>
          </div>
        </div>

        <!-- Assignment Section -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Assignment Section</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Assigned Staff</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select room attendant</option>
                <option>Blessing Okoro</option>
                <option>Ifeoma Nnadi</option>
                <option>Boma Eze</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Supervisor</p>
              <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select supervisor</option>
                <option>Housekeeping Supervisor</option>
              </select>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Start Time</p>
              <input type="text" placeholder="Select start time"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Expected Duration</p>
              <input type="text" value="45 mins"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
            </div>
          </div>
        </div>

        <!-- Inventory Update Section -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Inventory Update Section</h3>
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Item Replaced / Used</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Qty</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Store Impact</th>
                <th class="text-left text-xs font-medium text-gray-500 pb-2">Notes</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr>
                <td class="py-2.5 pr-3"><input type="text" value="Bath towel" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" /></td>
                <td class="py-2.5 pr-3"><input type="number" value="2" class="w-16 px-2 py-1.5 text-xs border border-gray-200 rounded text-center" /></td>
                <td class="py-2.5 pr-3"><button class="px-3 py-1.5 text-xs font-medium text-green-600 bg-green-50 rounded-lg">Reduce stock</button></td>
                <td class="py-2.5"><input type="text" value="Fresh set" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" /></td>
              </tr>
              <tr>
                <td class="py-2.5 pr-3"><input type="text" value="Toiletries pack" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" /></td>
                <td class="py-2.5 pr-3"><input type="number" value="1" class="w-16 px-2 py-1.5 text-xs border border-gray-200 rounded text-center" /></td>
                <td class="py-2.5 pr-3"><button class="px-3 py-1.5 text-xs font-medium text-green-600 bg-green-50 rounded-lg">Reduce stock</button></td>
                <td class="py-2.5"><input type="text" value="VIP pack" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded" /></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Housekeeping Checklist -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Housekeeping Checklist</h3>
          <div class="flex items-center gap-6">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked class="w-4 h-4 accent-green-500" />
              <span class="text-xs text-gray-700">Bed made and linen changed</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked class="w-4 h-4 accent-green-500" />
              <span class="text-xs text-gray-700">Bathroom sanitized</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" class="w-4 h-4 accent-green-500" />
              <span class="text-xs text-gray-700">Minibar checked</span>
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
              <option>Queued</option>
              <option>Inspection</option>
              <option>Released</option>
              <option>Suspended</option>
            </select>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Final Room Status</p>
            <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
              <option>Vacant Clean</option>
              <option>Vacant Dirty</option>
              <option>Occupied Clean</option>
              <option>Out of Order</option>
            </select>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Inspection Required</p>
            <label class="flex items-center gap-2 cursor-pointer bg-gray-50 rounded-lg px-3 py-2.5 border border-gray-200">
              <input type="checkbox" checked class="w-4 h-4 accent-green-500" />
              <span class="text-xs text-gray-700">Yes, supervisor must inspect</span>
            </label>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1.5">Task Completion Notes</p>
            <textarea rows="4" placeholder="Enter completion note, maintenance issue, lost item, or guest-related comment..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none"></textarea>
          </div>
          <div class="mb-4">
            <p class="text-xs text-gray-500 mb-1.5">Photo / Proof</p>
            <button class="w-full py-2.5 text-xs font-medium text-blue-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50">
              Upload room photo
            </button>
          </div>
        </div>

        <!-- Quick Summary -->
        <div class="bg-blue-50 rounded-xl border border-blue-100 p-4">
          <h4 class="text-xs font-bold text-blue-700 mb-2">Room 305 Task</h4>
          <p class="text-xs text-blue-600">Type: Checkout Cleaning</p>
          <p class="text-xs text-blue-600 mt-0.5">Assigned: Pending</p>
          <p class="text-xs text-blue-600 mt-0.5">Final status: Vacant Clean</p>
        </div>

        <!-- Related Actions -->
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <p class="text-xs font-semibold text-gray-700 mb-2">Related Actions</p>
          <div class="flex items-center gap-2">
            <button class="flex-1 py-2 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">Assign Staff</button>
            <button class="flex-1 py-2 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50">Request Supply</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>