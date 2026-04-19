<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Technician Summary</h2>
        <p class="text-xs text-gray-400 mt-0.5">TECH-00041 • Engr. Paul Okoro • in-house technician • currently available for assignment</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/maintenance/technicians')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Technician List</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Print</button>
        <button @click="showAssignModal = true" class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">Assign Task</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">Edit Profile</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Technician Type</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Employee</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">In-House</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Specialization</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Primary</span>
        </div>
        <p class="text-lg font-bold text-gray-900">Laundry / Mechanical</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Availability</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Ready</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">Available</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Open Assignments</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Live</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">2</p>
      </div>
    </div>

    <!-- Body -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:20px;">

      <!-- Left: Technician Details -->
      <div class="bg-white rounded-xl border border-gray-200 p-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Technician Details</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
          <div>
            <p class="text-xs text-gray-400 mb-1">Technician ID</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">TECH-00041</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Full Name / Company</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs font-semibold text-gray-900">Engr. Paul Okoro</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Technician Type</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">In-House Employee</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Source / Vendor</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">Employee Record</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Primary Specialization</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">Laundry / Mechanical</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Secondary Skills</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">Motor repair, pump service, inspections</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Phone</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">+234 803 222 1180</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Email</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">paul.okoro@hotel.local</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Availability Status</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-green-600 font-semibold">Available</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Shift / Schedule</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">08:00 AM - 05:00 PM</div>
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-400 mb-1">Notes</p>
          <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-600">
            Experienced laundry equipment technician. Handles urgent corrective work and preventive inspections for mechanical assets.
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-400 mb-1">Active Assignments</p>
          <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">
            MNT-000219 • Laundry Dryer motor failure | MNT-000214 • Booster pump servicing
          </div>
        </div>
      </div>

      <!-- Right: Performance & History -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Performance & History</h3>
          <div class="mb-3">
            <p class="text-xs text-gray-400 mb-1.5">Response Rating</p>
            <div class="bg-blue-50 rounded-lg px-3 py-2.5 text-xs font-semibold text-blue-600">4.8 / 5.0 average completion score</div>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-400 mb-1.5">Completed Tasks (30 days)</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">17 tasks completed</div>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-400 mb-1.5">Average Resolution Time</p>
            <div class="bg-gray-50 rounded-lg px-3 py-2.5 text-xs text-gray-700">16 hours</div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-2">Recent History</p>
            <div class="bg-gray-50 rounded-xl border border-gray-100 p-3 space-y-2">
              <div>
                <p class="text-xs font-semibold text-gray-900">18 Apr 2026</p>
                <p class="text-xs text-gray-400">Assigned to Laundry Dryer repair</p>
              </div>
              <div>
                <p class="text-xs font-semibold text-gray-900">17 Apr 2026</p>
                <p class="text-xs text-gray-400">Closed Smart TV service task</p>
              </div>
              <div>
                <p class="text-xs font-semibold text-gray-900">15 Apr 2026</p>
                <p class="text-xs text-gray-400">Completed preventive pump check</p>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <p class="text-xs font-semibold text-gray-700 mb-3">Quick Actions</p>
          <div class="space-y-2">
            <button class="w-full py-2.5 text-xs font-semibold text-red-500 border border-red-200 rounded-xl hover:bg-red-50">Mark Unavailable</button>
            <button class="w-full py-2.5 text-xs font-semibold text-white bg-green-500 rounded-xl hover:bg-green-600">Mark Available</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Assign Task Modal -->
    <Teleport to="body">
      <div v-if="showAssignModal" class="fixed inset-0 z-50 flex items-center justify-center" style="background:rgba(0,0,0,0.55);" @click.self="showAssignModal = false">
        <div class="bg-white rounded-2xl shadow-2xl w-full mx-4 overflow-y-auto" style="max-width:700px;max-height:90vh;">
          <div class="p-6">
            <div class="flex items-start justify-between mb-5">
              <div>
                <h2 class="text-lg font-bold text-gray-900">Assign Task</h2>
                <p class="text-xs text-gray-400 mt-1">Assign a maintenance work order to this technician and define the execution details.</p>
              </div>
              <div class="flex items-center gap-2">
                <button @click="showAssignModal = false" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Close</button>
                <button class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">Assign</button>
              </div>
            </div>

            <h3 class="text-sm font-bold text-gray-900 mb-3">Task Details</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Technician</p>
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold text-gray-900">Engr. Paul Okoro</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Technician Type</p>
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">In-House</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Availability</p>
                <div class="px-3 py-2.5 bg-green-50 border border-green-200 rounded-lg text-xs font-semibold text-green-600">Available for assignment</div>
              </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Task ID / Existing Task</p>
                <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                  <option value="">Select maintenance task</option>
                  <option>MNT-000219 - Laundry Dryer</option>
                  <option>MNT-000218 - Generator Bank</option>
                  <option>MNT-000216 - Room 214 AC</option>
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
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Task Type</p>
                <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                  <option>Corrective Maintenance</option>
                  <option>Preventive Maintenance</option>
                  <option>Inspection</option>
                </select>
              </div>
            </div>

            <div class="mb-4">
              <p class="text-xs text-gray-500 mb-1.5">Asset / Issue</p>
              <div class="px-3 py-3 bg-gray-50 border border-gray-200 rounded-lg">
                <p class="text-xs font-semibold text-gray-900">Industrial Laundry Dryer - Motor Failure</p>
                <p class="text-xs text-gray-400 mt-0.5">Laundry Room • reported vibration, overheating, and intermittent shutdown during operation.</p>
              </div>
            </div>

            <h3 class="text-sm font-bold text-gray-900 mb-3">Assignment Setup</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Planned Start</p>
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">18 Apr 2026 • 10:30 AM</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Expected Duration</p>
                <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">3 hrs</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Supervisor</p>
                <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-700">
                  <option>Maintenance Supervisor</option>
                </select>
              </div>
            </div>

            <div class="mb-5">
              <p class="text-xs text-gray-500 mb-1.5">Assignment Note</p>
              <textarea rows="3" placeholder="Add technician instructions, access note, expected caution, or troubleshooting direction..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none resize-none"></textarea>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
              <div class="bg-gray-50 rounded-xl border border-gray-100 p-3">
                <p class="text-xs text-gray-400 mb-1">Current Open Tasks</p>
                <p class="text-sm font-bold text-gray-900">2 active assignments</p>
              </div>
              <div class="bg-gray-50 rounded-xl border border-gray-100 p-3">
                <p class="text-xs text-gray-400 mb-1">Last Completion Score</p>
                <p class="text-sm font-bold text-gray-900">4.8 / 5.0</p>
              </div>
              <div class="bg-blue-50 rounded-xl border border-blue-100 p-3">
                <p class="text-xs text-blue-500 mb-1">Recommendation</p>
                <p class="text-xs font-bold text-blue-700">Suitable for urgent mechanical task</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showAssignModal = ref(false)
</script>