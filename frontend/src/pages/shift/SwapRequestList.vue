<template>
  <div class="space-y-5">

    <!-- Subtitle -->
    <div>
      <p class="text-xs text-gray-400">Review staff requests to swap shifts, validate availability and conflicts, then approve, reject, or request revision.</p>
    </div>

    <!-- Swap Request Control -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Swap Request Control</h3>
      <p class="text-xs text-gray-400 mt-0.5 mb-4">Track pending, approved, rejected, and conflict-flagged shift swap requests for a selected specific date.</p>

      <div class="flex items-end gap-3 flex-wrap">
        <div style="min-width:160px;">
          <p class="text-xs text-gray-500 mb-1.5">Department</p>
          <select v-model="department" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option v-for="dept in departmentOptions" :key="dept" :value="dept">{{ dept }}</option>
          </select>
        </div>
        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Specific Date</p>
          <input v-model="specificDate" type="text" readonly
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 bg-white" />
        </div>
        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Status</p>
          <select v-model="statusFilter" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option v-for="opt in statusOptions" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </div>
        <div class="flex-1" style="min-width:200px;">
          <p class="text-xs text-gray-500 mb-1.5">&nbsp;</p>
          <input v-model="searchText" type="text" placeholder="Search staff, request ID..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>

        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="resetFilters">Reset</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
          @click="exportRequests">Export</button>
        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="goToShiftList">Shift List</button>
        <button
          class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap"
          @click="newSwapRequest">New Swap Request</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Pending Review</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-600 rounded-full">Queue</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.pendingReview }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Approved This Week</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Approved</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.approvedThisWeek }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Conflict Alerts</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-600 rounded-full">Risk</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.conflictAlerts }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Rejected / Cancelled</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Closed</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ stats.rejectedCancelled }}</p>
      </div>
    </div>

    <!-- Swap Request Records -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h3 class="text-sm font-bold text-gray-900">Swap Request Records</h3>
        <p class="text-xs text-gray-400">Showing 1–{{ swapRequests.length }} of {{ totalRequests }} requests</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full border-collapse" style="min-width:1200px;">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-l-lg">Request ID</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Requester</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Department</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Original Shift / Date</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Swap With</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Requested Shift / Date</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Check</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Status</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 rounded-r-lg">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in swapRequests" :key="row.id" class="border-b border-gray-100">
              <td class="px-3 py-3.5 text-sm font-bold text-gray-900">{{ row.id }}</td>
              <td class="px-3 py-3.5">
                <p class="text-sm font-bold text-gray-900">{{ row.requester }}</p>
                <p class="text-xs text-gray-400">{{ row.requesterRole }}</p>
              </td>
              <td class="px-3 py-3.5 text-sm text-gray-500">{{ row.department }}</td>
              <td class="px-3 py-3.5">
                <p class="text-sm text-gray-700">{{ row.originalShift.label }}</p>
                <p class="text-xs text-gray-400">{{ row.originalShift.time }}</p>
              </td>
              <td class="px-3 py-3.5 text-sm text-gray-700">{{ row.swapWith }}</td>
              <td class="px-3 py-3.5">
                <p class="text-sm text-gray-700">{{ row.requestedShift.label }}</p>
                <p class="text-xs text-gray-400">{{ row.requestedShift.time }}</p>
              </td>
              <td class="px-3 py-3.5">
                <span :class="['px-2.5 py-0.5 text-xs font-medium rounded-full', checkClass(row.check)]">{{ row.check }}</span>
              </td>
              <td class="px-3 py-3.5">
                <span :class="['px-2.5 py-0.5 text-xs font-medium rounded-full', statusClass(row.status)]">{{ row.status }}</span>
              </td>
              <td class="px-3 py-3.5">
                <button
                  :class="['px-4 py-1.5 text-xs font-medium rounded-lg transition-colors', row.status === 'Pending' ? 'text-white bg-blue-600 hover:bg-blue-700' : 'text-gray-700 border border-gray-300 hover:bg-gray-50']"
                  @click="viewRequest(row)">View</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Footer: pagination -->
      <div class="flex items-center justify-between flex-wrap gap-2 mt-5 pt-4 border-t border-gray-100">
        <p class="text-xs text-gray-400">Rows per page: 25 &bull; Showing swap requests for selected specific date</p>

        <div class="flex items-center gap-2">
          <button
            v-for="page in pageNumbers"
            :key="page"
            :class="['w-7 h-7 text-xs font-medium rounded-lg transition-colors', currentPage === page ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100']"
            @click="currentPage = page">{{ page }}</button>
          <button
            class="px-4 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            @click="nextPage">Next</button>
        </div>
      </div>
    </div>

    <!-- Review Swap Request Modal -->
    <Teleport to="body" v-if="activeRequest">
      <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
        style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
        @click.self="activeRequest = null">
        <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:760px;max-height:92vh;">

          <!-- Header -->
          <div class="px-8 pt-7 pb-5 flex items-start justify-between border-b border-gray-100">
            <div>
              <h2 class="text-2xl font-bold text-gray-900">Review Swap Request</h2>
              <p class="text-xs text-gray-400 mt-1">Review details, conflict checks, availability, manager notes, and approve or reject the staff shift swap.</p>
            </div>
            <button @click="activeRequest = null"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex-shrink-0">Close</button>
          </div>

          <div class="px-8 py-6 space-y-5">

            <!-- Request Summary -->
            <div class="bg-gray-50 rounded-xl border border-gray-100 px-5 py-4 flex items-center justify-between flex-wrap gap-4">
              <div>
                <h3 class="text-sm font-bold text-gray-900 mb-3">Request Summary</h3>
                <div class="flex items-center gap-10 flex-wrap">
                  <div>
                    <p class="text-xs text-gray-400">Request ID</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.id }}</p>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400">Department</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.department }}</p>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400">Submitted On</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.submittedOn }}</p>
                  </div>
                </div>
              </div>
              <span class="px-3 py-1.5 text-xs font-semibold bg-amber-100 text-amber-700 rounded-lg">{{ activeRequest.status }}</span>
            </div>

            <!-- Original / Requested Shift -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <h3 class="text-sm font-bold text-gray-900 mb-3">Original Shift</h3>
                <div class="space-y-3">
                  <div>
                    <p class="text-xs text-gray-400">Requester</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.original.requester }}</p>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400">Role / Station</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.original.roleStation }}</p>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400">Shift Date / Time</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.original.shiftDateTime }}</p>
                  </div>
                </div>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <h3 class="text-sm font-bold text-gray-900 mb-3">Requested Swap Shift</h3>
                <div class="space-y-3">
                  <div>
                    <p class="text-xs text-gray-400">Swap With</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.swap.swapWith }}</p>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400">Role / Station</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.swap.roleStation }}</p>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400">Shift Date / Time</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.swap.shiftDateTime }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Availability & Conflict Check -->
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Availability &amp; Conflict Check</h3>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
                <div v-for="(check, idx) in activeRequest.checks" :key="idx"
                  :class="['rounded-xl px-4 py-3', checkBg(check.level)]">
                  <p class="text-sm font-bold" :class="checkTitleColor(check.level)">{{ check.title }}</p>
                  <p class="text-xs mt-1" :class="checkBodyColor(check.level)">{{ check.detail }}</p>
                </div>
              </div>
            </div>

            <!-- Request Reason / Manager Decision -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <h3 class="text-sm font-bold text-gray-900 mb-3">Request Reason</h3>
                <div class="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
                  <p class="text-xs text-gray-500">{{ activeRequest.reason }}</p>
                </div>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <h3 class="text-sm font-bold text-gray-900 mb-3">Manager Decision</h3>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                  <div>
                    <p class="text-xs font-semibold text-gray-700 mb-1.5">Decision Status</p>
                    <div class="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5">
                      <p class="text-xs text-gray-400">{{ activeRequest.decisionStatus }}</p>
                    </div>
                  </div>
                  <div>
                    <p class="text-xs font-semibold text-gray-700 mb-1.5">Effective Status</p>
                    <div class="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5">
                      <p class="text-xs text-gray-400">{{ activeRequest.effectiveStatus }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Manager Review Note -->
            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Manager Review Note</h3>
              <input v-model="reviewNote" type="text" placeholder="Add approval/rejection note for audit trail..."
                class="w-full px-4 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

          </div>

          <!-- Footer Actions -->
          <div class="px-8 py-5 bg-gray-50 border-t border-gray-100 flex items-center justify-end gap-3">
            <button
              class="px-6 py-2.5 text-xs font-semibold text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
              @click="onReject">Reject</button>
            <button
              class="px-6 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
              @click="onApprove">Approve Swap</button>
          </div>

        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const departmentOptions = ['All Departments', 'Housekeeping', 'Front Desk', 'Security', 'POS / Restaurant', 'Maintenance']
const department = ref('All Departments')
const specificDate = ref('18 Apr 2026')

const statusOptions = ['All Statuses', 'Pending', 'Approved', 'Rejected']
const statusFilter = ref('All Statuses')

const searchText = ref('')

const stats = reactive({
  pendingReview: 7,
  approvedThisWeek: 12,
  conflictAlerts: 3,
  rejectedCancelled: 4,
})

const totalRequests = ref(23)

const swapRequests = reactive([
  {
    id: 'SWP-000184',
    requester: 'Mary Bello',
    requesterRole: 'Room Attendant',
    department: 'Housekeeping',
    originalShift: { label: '18 Apr 2026 • Morning', time: '8:00 AM - 4:00 PM' },
    swapWith: 'Tina Okafor',
    requestedShift: { label: '18 Apr 2026 • Afternoon', time: '12:00 PM - 8:00 PM' },
    check: 'Clear',
    status: 'Pending',
  },
  {
    id: 'SWP-000183',
    requester: 'Chinedu Nwosu',
    requesterRole: 'Night Cleaner',
    department: 'Housekeeping',
    originalShift: { label: '18 Apr 2026 • Night', time: '8:00 PM - 8:00 AM' },
    swapWith: 'Sarah Musa',
    requestedShift: { label: '19 Apr 2026 • Night', time: '8:00 PM - 8:00 AM' },
    check: 'Conflict',
    status: 'Pending',
  },
  {
    id: 'SWP-000182',
    requester: 'Rita James',
    requesterRole: 'Room Attendant',
    department: 'Housekeeping',
    originalShift: { label: '16 Apr 2026 • Morning', time: '8:00 AM - 4:00 PM' },
    swapWith: 'Kemi Yusuf',
    requestedShift: { label: '16 Apr 2026 • Afternoon', time: '12:00 PM - 8:00 PM' },
    check: 'Clear',
    status: 'Approved',
  },
  {
    id: 'SWP-000181',
    requester: 'Amaka Eze',
    requesterRole: 'Receptionist',
    department: 'Front Desk',
    originalShift: { label: '17 Apr 2026 • Morning', time: '7:00 AM - 3:00 PM' },
    swapWith: 'Rita Adams',
    requestedShift: { label: '17 Apr 2026 • Evening', time: '3:00 PM - 11:00 PM' },
    check: 'Clear',
    status: 'Rejected',
  },
  {
    id: 'SWP-000180',
    requester: 'John Ude',
    requesterRole: 'Laundry Attendant',
    department: 'Housekeeping',
    originalShift: { label: '15 Apr 2026 • Morning', time: '8:00 AM - 4:00 PM' },
    swapWith: 'Mary Bello',
    requestedShift: { label: '15 Apr 2026 • Off Day', time: 'Replacement Cover' },
    check: 'Review',
    status: 'Pending',
  },
  {
    id: 'SWP-000179',
    requester: 'Ibrahim Musa',
    requesterRole: 'Security Officer',
    department: 'Security',
    originalShift: { label: '18 Apr 2026 • Night', time: '8:00 PM - 8:00 AM' },
    swapWith: 'Tunde Obi',
    requestedShift: { label: '19 Apr 2026 • Night', time: '8:00 PM - 8:00 AM' },
    check: 'Clear',
    status: 'Approved',
  },
  {
    id: 'SWP-000178',
    requester: 'Peter Okon',
    requesterRole: 'POS Cashier',
    department: 'POS / Restaurant',
    originalShift: { label: '13 Apr 2026 • Evening', time: '4:00 PM - 12:00 AM' },
    swapWith: 'Joy Samuel',
    requestedShift: { label: '14 Apr 2026 • Evening', time: '4:00 PM - 12:00 AM' },
    check: 'Clear',
    status: 'Pending',
  },
])

const currentPage = ref(1)
const pageNumbers = [1, 2, 3]

const activeRequest = ref(null)
const reviewNote = ref('')

const checkDetails = {
  Clear: { level: 'success', title: 'No Overlap Conflict', detail: 'Both shifts are valid for the selected date.' },
  Conflict: { level: 'warning', title: 'Schedule Conflict Detected', detail: 'Requested shift overlaps with an existing assignment.' },
  Review: { level: 'warning', title: 'Manager Review Needed', detail: 'Coverage or role change requires manager sign-off.' },
}

function buildRequestDetail(row) {
  return {
    id: row.id,
    department: row.department,
    submittedOn: '18 Apr 2026 • 9:20 AM',
    status: row.status === 'Pending' ? 'Pending Review' : row.status,
    original: {
      requester: row.requester,
      roleStation: row.roleStation,
      shiftDateTime: `${row.originalShift.label.replace(' • ', ' • ')} • ${row.originalShift.time}`,
    },
    swap: {
      swapWith: row.swapWith,
      roleStation: row.roleStation,
      shiftDateTime: `${row.requestedShift.label.replace(' • ', ' • ')} • ${row.requestedShift.time}`,
    },
    checks: [
      { level: 'success', title: 'No Overlap Conflict', detail: 'Both shifts are valid for the selected date.' },
      { level: 'success', title: 'Both Staff Available', detail: 'No leave or blocked schedule found.' },
      checkDetails[row.check] || checkDetails.Review,
    ],
    reason: 'I has a family appointment during the morning shift and has agreed with the swap staff to exchange duty time.',
    decisionStatus: row.status === 'Pending' ? 'Pending Review' : row.status,
    effectiveStatus: row.status === 'Pending' ? 'Updates after approval' : 'Applied to schedule',
  }
}


function checkClass(value) {
  switch (value) {
    case 'Clear':
      return 'bg-green-100 text-green-600'
    case 'Conflict':
      return 'bg-red-100 text-red-600'
    case 'Review':
      return 'bg-amber-100 text-amber-600'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

function statusClass(value) {
  switch (value) {
    case 'Approved':
      return 'bg-green-100 text-green-600'
    case 'Pending':
      return 'bg-amber-100 text-amber-600'
    case 'Rejected':
      return 'bg-red-100 text-red-600'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

function resetFilters() {
  department.value = 'All Departments'
  specificDate.value = '18 Apr 2026'
  statusFilter.value = 'All Statuses'
  searchText.value = ''
}

function exportRequests() {
  // No backend connected — placeholder for export action
}

function goToShiftList() {
  // No backend connected — placeholder for navigation to Shift List
}

function newSwapRequest() {
  // No backend connected — placeholder for new swap request action
}

function viewRequest(row) {
  activeRequest.value = buildRequestDetail(row)
  reviewNote.value = ''
}

function checkBg(level) {
  return level === 'warning' ? 'bg-amber-50' : 'bg-green-50'
}
function checkTitleColor(level) {
  return level === 'warning' ? 'text-amber-700' : 'text-green-700'
}
function checkBodyColor(level) {
  return level === 'warning' ? 'text-amber-600' : 'text-green-600'
}

function onApprove() {
  const row = swapRequests.find((r) => r.id === activeRequest.value.id)
  if (row) row.status = 'Approved'
  activeRequest.value = null
}

function onReject() {
  const row = swapRequests.find((r) => r.id === activeRequest.value.id)
  if (row) row.status = 'Rejected'
  activeRequest.value = null
}

function nextPage() {
  if (currentPage.value < pageNumbers.length) currentPage.value += 1
}
</script>