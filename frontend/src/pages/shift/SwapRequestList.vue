<template>
  <div class="space-y-5">
    <div
      v-if="showToast"
      class="fixed top-5 right-5 z-[70] text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-lg"
      :class="toastType === 'error' ? 'bg-red-600' : 'bg-green-600'"
    >
      {{ toastMessage }}
    </div>

    <div>
      <p class="text-xs text-gray-400">
        Staff can request shift swaps. Managers review, approve, or reject.
      </p>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900">Swap Request Control</h3>

      <div class="flex items-end gap-3 flex-wrap mt-4">
        <div style="min-width:180px;">
          <p class="text-xs text-gray-500 mb-1.5">Department</p>
          <select
            v-model="filters.department"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg"
          >
            <option value="All Departments">All Departments</option>
            <option v-for="dept in departments" :key="dept" :value="dept">
              {{ dept }}
            </option>
          </select>
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Specific Date</p>
          <input
            v-model="filters.date"
            type="date"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg"
          />
        </div>

        <div style="min-width:150px;">
          <p class="text-xs text-gray-500 mb-1.5">Status</p>
          <select
            v-model="filters.status"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg"
          >
            <option>All Statuses</option>
            <option>Pending</option>
            <option>Approved</option>
            <option>Rejected</option>
            <option>Cancelled</option>
          </select>
        </div>

        <div class="flex-1" style="min-width:200px;">
          <p class="text-xs text-gray-500 mb-1.5">&nbsp;</p>
          <input
            v-model="filters.search"
            type="text"
            placeholder="Search staff, request ID..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg"
          />
        </div>

        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
          @click="resetFilters"
        >
          Reset
        </button>

        <button
          class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
          @click="loadPage"
        >
          Refresh
        </button>

       <button
        v-if="myContext.has_employee"
        class="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700"
        @click="openNewModal"
      >
        New Swap Request
      </button>
      </div>
    </div>

    <div v-if="myContext.is_manager" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-3">Pending Review</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.pendingReview }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-3">Approved</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.approvedThisWeek }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-3">Conflict Alerts</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.conflictAlerts }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <p class="text-xs text-gray-400 mb-3">Rejected / Cancelled</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.rejectedCancelled }}</p>
      </div>
    </div>

   <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <h3 class="text-sm font-bold text-gray-900 mb-4">Swap Request Records</h3>

      <div v-if="loading" class="py-10 text-center text-xs text-gray-400">
        Loading requests...
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full border-collapse" style="min-width:1200px;">
          <thead>
            <tr class="bg-gray-50">
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Request ID</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Requester</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Department</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Original Shift</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Swap With</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Requested Shift</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Check</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Status</th>
              <th class="text-left px-3 py-2.5 text-xs font-semibold text-gray-500">Action</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="row in requests" :key="row.name" class="border-b border-gray-100">
              <td class="px-3 py-3.5 text-sm font-bold text-gray-900">{{ row.request_id }}</td>

              <td class="px-3 py-3.5">
                <p class="text-sm font-bold text-gray-900">{{ row.requesting_employee_name }}</p>
                <p class="text-xs text-gray-400">{{ row.requesting_employee }}</p>
              </td>

              <td class="px-3 py-3.5 text-sm text-gray-500">{{ row.department }}</td>

              <td class="px-3 py-3.5">
                <p class="text-sm text-gray-700">{{ row.date }} • {{ row.requesting_shift }}</p>
                <p class="text-xs text-gray-400">{{ row.requesting_shift_time || 'No time' }}</p>
              </td>

              <td class="px-3 py-3.5">
                <p class="text-sm font-bold text-gray-900">{{ row.target_employee_name }}</p>
                <p class="text-xs text-gray-400">{{ row.target_employee }}</p>
              </td>

              <td class="px-3 py-3.5">
                <p class="text-sm text-gray-700">{{ row.date }} • {{ row.target_shift }}</p>
                <p class="text-xs text-gray-400">{{ row.target_shift_time || 'No time' }}</p>
              </td>

              <td class="px-3 py-3.5">
                <span :class="['px-2.5 py-0.5 text-xs font-medium rounded-full', checkClass(row.check_status)]">
                  {{ row.check_status }}
                </span>
              </td>

              <td class="px-3 py-3.5">
                <span :class="['px-2.5 py-0.5 text-xs font-medium rounded-full', statusClass(row.status)]">
                  {{ row.status }}
                </span>
              </td>

              <td class="px-3 py-3.5">
                <button
                  class="px-4 py-1.5 text-xs font-medium rounded-lg text-gray-700 border border-gray-300 hover:bg-gray-50"
                  @click="viewRequest(row.name)"
                >
                  View
                </button>
              </td>
            </tr>

            <tr v-if="!requests.length">
              <td colspan="9" class="py-8 text-center text-xs text-gray-400">
                No swap requests found.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>


    <!-- New Swap Request Modal -->
    <Teleport to="body" v-if="showNewModal">
      <div
        class="fixed inset-0 z-50 flex items-center justify-center p-6"
        style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
        @click.self="closeNewModal"
      >
        <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:820px;max-height:92vh;">
          <div class="px-8 pt-7 pb-5 flex items-start justify-between border-b border-gray-100">
            <div>
              <h2 class="text-2xl font-bold text-gray-900">New Swap Request</h2>
              <p class="text-xs text-gray-400 mt-1">
                Your employee and department are set automatically from your logged-in user.
              </p>
            </div>

            <button
              @click="closeNewModal"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Close
            </button>
          </div>

          <div class="px-8 py-6 space-y-5">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
              <div>
                <p class="text-xs font-semibold text-gray-700 mb-1.5">Department</p>
                <input
                  v-model="myContext.department"
                  readonly
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-100"
                />
              </div>

              <div>
                <p class="text-xs font-semibold text-gray-700 mb-1.5">Swap Date *</p>
                <input
                  v-model="newForm.date"
                  type="date"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg"
                />
              </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
              <div class="bg-gray-50 rounded-xl border border-gray-100 px-5 py-4">
                <h3 class="text-sm font-bold text-gray-900 mb-3">Requesting Employee</h3>

                <input
                  :value="`${myContext.employee_name} (${myContext.employee})`"
                  readonly
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-100"
                />

                <div v-if="requestingShift" class="mt-3 bg-white border border-gray-200 rounded-lg px-4 py-3">
                  <p class="text-xs text-gray-400 mb-1">Current Shift</p>
                  <p class="text-sm font-bold text-gray-900">{{ requestingShift.value }}</p>
                  <p class="text-xs text-gray-500">{{ requestingShift.time || 'No time' }}</p>
                </div>
              </div>

              <div class="bg-gray-50 rounded-xl border border-gray-100 px-5 py-4">
                <h3 class="text-sm font-bold text-gray-900 mb-3">Target Employee</h3>

                <select
                  v-model="newForm.target_employee"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg"
                >
                  <option value="">Select target employee</option>
                  <option v-for="emp in targetEmployees" :key="emp.employee" :value="emp.employee">
                    {{ emp.employee_name }}{{ emp.designation ? ` - ${emp.designation}` : '' }}
                  </option>
                </select>

                <div v-if="targetShift" class="mt-3 bg-white border border-gray-200 rounded-lg px-4 py-3">
                  <p class="text-xs text-gray-400 mb-1">Current Shift</p>
                  <p class="text-sm font-bold text-gray-900">{{ targetShift.value }}</p>
                  <p class="text-xs text-gray-500">{{ targetShift.time || 'No time' }}</p>
                </div>
              </div>
            </div>

            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Availability &amp; Conflict Check</h3>

              <div v-if="checking" class="text-xs text-gray-400">Checking availability...</div>

              <div v-else-if="checks.length" style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
                <div
                  v-for="(check, idx) in checks"
                  :key="idx"
                  :class="['rounded-xl px-4 py-3', checkBg(check.level)]"
                >
                  <p class="text-sm font-bold" :class="checkTitleColor(check.level)">
                    {{ check.title }}
                  </p>
                  <p class="text-xs mt-1" :class="checkBodyColor(check.level)">
                    {{ check.detail }}
                  </p>
                </div>
              </div>

              <p v-else class="text-xs text-gray-400">
                Select date and target employee to run check.
              </p>
            </div>

            <div>
              <p class="text-xs font-semibold text-gray-700 mb-1.5">Request Reason *</p>
              <textarea
                v-model="newForm.request_reason"
                rows="3"
                placeholder="Enter reason for this swap request..."
                class="w-full px-4 py-2.5 text-xs border border-gray-200 rounded-lg"
              />
            </div>
          </div>

          <div class="px-8 py-5 bg-gray-50 border-t border-gray-100 flex items-center justify-end gap-3">
            <button
              class="px-6 py-2.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              @click="closeNewModal"
            >
              Cancel
            </button>

            <button
              class="px-6 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              :disabled="!canCreateRequest || creating"
              @click="createRequest"
            >
              {{ creating ? 'Creating...' : 'Create Request' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Manager View Modal -->
    <Teleport to="body" v-if="activeRequest">
      <div
        class="fixed inset-0 z-50 flex items-center justify-center p-6"
        style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
        @click.self="activeRequest = null"
      >
        <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:760px;max-height:92vh;">
          <div class="px-8 pt-7 pb-5 flex items-start justify-between border-b border-gray-100">
            <div>
              <h2 class="text-2xl font-bold text-gray-900">Review Swap Request</h2>
              <p class="text-xs text-gray-400 mt-1">
                Review details, conflict checks, manager notes, and approve or reject.
              </p>
            </div>

            <button
              @click="activeRequest = null"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Close
            </button>
          </div>

          <div class="px-8 py-6 space-y-5">
            <div class="bg-gray-50 rounded-xl border border-gray-100 px-5 py-4 flex items-center justify-between">
              <div>
                <h3 class="text-sm font-bold text-gray-900 mb-3">Request Summary</h3>
                <div class="flex items-center gap-10 flex-wrap">
                  <div>
                    <p class="text-xs text-gray-400">Request ID</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.request_id }}</p>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400">Department</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.department }}</p>
                  </div>
                  <div>
                    <p class="text-xs text-gray-400">Date</p>
                    <p class="text-sm font-bold text-gray-900">{{ activeRequest.date }}</p>
                  </div>
                </div>
              </div>

              <span :class="['px-3 py-1.5 text-xs font-semibold rounded-lg', statusClass(activeRequest.status)]">
                {{ activeRequest.status }}
              </span>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <h3 class="text-sm font-bold text-gray-900 mb-3">Original Shift</h3>
                <p class="text-xs text-gray-400">Requester</p>
                <p class="text-sm font-bold text-gray-900 mb-3">{{ activeRequest.requesting_employee_name }}</p>
                <p class="text-xs text-gray-400">Shift Date / Time</p>
                <p class="text-sm font-bold text-gray-900">
                  {{ activeRequest.date }} • {{ activeRequest.requesting_shift }} • {{ activeRequest.requesting_shift_time || 'No time' }}
                </p>
              </div>

              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <h3 class="text-sm font-bold text-gray-900 mb-3">Requested Swap Shift</h3>
                <p class="text-xs text-gray-400">Swap With</p>
                <p class="text-sm font-bold text-gray-900 mb-3">{{ activeRequest.target_employee_name }}</p>
                <p class="text-xs text-gray-400">Shift Date / Time</p>
                <p class="text-sm font-bold text-gray-900">
                  {{ activeRequest.date }} • {{ activeRequest.target_shift }} • {{ activeRequest.target_shift_time || 'No time' }}
                </p>
              </div>
            </div>

            <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
              <h3 class="text-sm font-bold text-gray-900 mb-3">Availability &amp; Conflict Check</h3>

              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
                <div
                  v-for="(check, idx) in activeRequest.checks || []"
                  :key="idx"
                  :class="['rounded-xl px-4 py-3', checkBg(check.level)]"
                >
                  <p class="text-sm font-bold" :class="checkTitleColor(check.level)">
                    {{ check.title }}
                  </p>
                  <p class="text-xs mt-1" :class="checkBodyColor(check.level)">
                    {{ check.detail }}
                  </p>
                </div>
              </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <h3 class="text-sm font-bold text-gray-900 mb-3">Request Reason</h3>
                <div class="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
                  <p class="text-xs text-gray-500">{{ activeRequest.request_reason }}</p>
                </div>
              </div>

              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <h3 class="text-sm font-bold text-gray-900 mb-3">Manager Review Note</h3>
                <textarea
  v-model="reviewNote"
  rows="4"
  :readonly="activeRequest.status !== 'Pending'"
  :disabled="activeRequest.status !== 'Pending'"
  :placeholder="activeRequest.status === 'Pending'
    ? 'Add approval/rejection note...'
    : 'Request is closed. Manager note cannot be edited.'"
  class="w-full px-4 py-2.5 text-xs border border-gray-200 rounded-lg"
  :class="activeRequest.status !== 'Pending'
    ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
    : 'bg-white'"
/>
              </div>
            </div>
          </div>

          <div
            v-if="activeRequest.status === 'Pending'"
            class="px-8 py-5 bg-gray-50 border-t border-gray-100 flex items-center justify-end gap-3"
          >
            <button
              class="px-6 py-2.5 text-xs font-semibold text-red-600 bg-red-50 rounded-lg hover:bg-red-100"
              @click="rejectRequest"
            >
              Reject
            </button>

            <button
              class="px-6 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700"
              @click="approveRequest"
            >
              Approve Swap
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { callMethod } from '@/lib/api'

function todayIso() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const myContext = reactive({
  employee: '',
  employee_name: '',
  designation: '',
  department: '',
  company: '',
  is_manager: false,
})

const requests = ref([])
const totalRequests = ref(0)
const loading = ref(false)
const page = ref(1)
const pageLength = ref(25)

const departments = ref([])

async function loadDepartments() {
  departments.value = await callMethod('rhohotel.rhocom_hotel.api.swap_request.get_departments') || []
}

const filters = reactive({
  department: 'All Departments',
  date: todayIso(),
  status: 'All Statuses',
  search: '',
})

const stats = reactive({
  pendingReview: 0,
  approvedThisWeek: 0,
  conflictAlerts: 0,
  rejectedCancelled: 0,
})

const showNewModal = ref(false)

const newForm = reactive({
  date: todayIso(),
  target_employee: '',
  request_reason: '',
})

const targetEmployees = ref([])
const requestingShift = ref(null)
const targetShift = ref(null)
const checks = ref([])
const checkOk = ref(false)
const checking = ref(false)
const creating = ref(false)

const activeRequest = ref(null)
const reviewNote = ref('')

const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('success')
let toastTimer = null

const canCreateRequest = computed(() => {
  return (
    myContext.employee &&
    myContext.department &&
    newForm.date &&
    newForm.target_employee &&
    newForm.request_reason.trim() &&
    checkOk.value
  )
})

function toast(message, type = 'success') {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    showToast.value = false
  }, 3000)
}

async function loadMyContext() {
  const ctx = await callMethod('rhohotel.rhocom_hotel.api.swap_request.get_my_swap_context')
  Object.assign(myContext, ctx || {})
}

async function loadPage() {
  loading.value = true

  try {
    const res = await callMethod('rhohotel.rhocom_hotel.api.swap_request.get_swap_requests', {
      department: filters.department,
      date: filters.date,
      status: filters.status,
      search: filters.search,
      limit_start: (page.value - 1) * pageLength.value,
      limit_page_length: pageLength.value,
    })

    requests.value = res?.rows || []
    totalRequests.value = res?.total || 0

    if (myContext.is_manager) {
      const s = await callMethod('rhohotel.rhocom_hotel.api.swap_request.get_swap_request_stats', {
        department: filters.department,
        date: filters.date,
      })

      Object.assign(stats, s || {})
    }
  } catch (e) {
    toast(e.message || 'Failed to load swap requests.', 'error')
  } finally {
    loading.value = false
  }
}


async function loadEmployeesForNewModal() {
  if (!myContext.department) {
    targetEmployees.value = []
    return
  }

  targetEmployees.value = await callMethod(
    'rhohotel.rhocom_hotel.api.swap_request.get_department_employees',
    {
      department: myContext.department,
      exclude_employee: myContext.employee,
    }
  ) || []
}

async function loadEmployeeShifts() {
  requestingShift.value = null
  targetShift.value = null

  if (myContext.employee && newForm.date) {
    requestingShift.value = await callMethod('rhohotel.rhocom_hotel.api.swap_request.get_employee_shift', {
      employee: myContext.employee,
      date: newForm.date,
    })
  }

  if (newForm.target_employee && newForm.date) {
    targetShift.value = await callMethod('rhohotel.rhocom_hotel.api.swap_request.get_employee_shift', {
      employee: newForm.target_employee,
      date: newForm.date,
    })
  }
}

async function runAvailabilityCheck() {
  checks.value = []
  checkOk.value = false

  if (!newForm.date || !newForm.target_employee) return

  checking.value = true

  try {
    const res = await callMethod('rhohotel.rhocom_hotel.api.swap_request.check_swap_availability', {
      date: newForm.date,
      target_employee: newForm.target_employee,
    })

    checks.value = res?.checks || []
    checkOk.value = !!res?.ok
  } catch (e) {
    checks.value = [{
      level: 'warning',
      title: 'Conflict',
      detail: e.message || 'Unable to validate swap request.',
    }]
    checkOk.value = false
  } finally {
    checking.value = false
  }
}

watch(
  () => [newForm.target_employee, newForm.date],
  async () => {
    await loadEmployeeShifts()
    await runAvailabilityCheck()
  }
)

watch(
  () => [filters.department, filters.date, filters.status],
  () => {
    page.value = 1
    loadPage()
  }
)

let searchTimer = null
watch(
  () => filters.search,
  () => {
    clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      page.value = 1
      loadPage()
    }, 400)
  }
)

async function openNewModal() {
  showNewModal.value = true

  await loadMyContext()

  newForm.date = filters.date || todayIso()
  newForm.target_employee = ''
  newForm.request_reason = ''
  requestingShift.value = null
  targetShift.value = null
  checks.value = []
  checkOk.value = false

  await loadEmployeesForNewModal()
  await loadEmployeeShifts()
}

function closeNewModal() {
  showNewModal.value = false
}

async function createRequest() {
  if (!canCreateRequest.value) return

  creating.value = true

  try {
    await callMethod('rhohotel.rhocom_hotel.api.swap_request.create_swap_request', {
      date: newForm.date,
      target_employee: newForm.target_employee,
      request_reason: newForm.request_reason,
    })

    toast('Swap request created.')
    closeNewModal()
    await loadPage()
  } catch (e) {
    toast(e.message || 'Failed to create swap request.', 'error')
  } finally {
    creating.value = false
  }
}

async function viewRequest(name) {
  try {
    activeRequest.value = await callMethod('rhohotel.rhocom_hotel.api.swap_request.get_swap_request', {
      name,
    })
    reviewNote.value = ''
  } catch (e) {
    toast(e.message || 'Failed to open request.', 'error')
  }
}

async function approveRequest() {
  if (!activeRequest.value) return

  try {
    await callMethod('rhohotel.rhocom_hotel.api.swap_request.approve_swap_request', {
      name: activeRequest.value.name,
      manager_note: reviewNote.value || '',
    })

    toast('Swap approved and applied.')
    activeRequest.value = null
    await loadPage()
  } catch (e) {
    toast(e.message || 'Failed to approve swap.', 'error')
  }
}

async function rejectRequest() {
  if (!activeRequest.value) return

  try {
    await callMethod('rhohotel.rhocom_hotel.api.swap_request.reject_swap_request', {
      name: activeRequest.value.name,
      manager_note: reviewNote.value || '',
    })

    toast('Swap request rejected.')
    activeRequest.value = null
    await loadPage()
  } catch (e) {
    toast(e.message || 'Failed to reject request.', 'error')
  }
}

function resetFilters() {
  filters.department = 'All Departments'
  filters.date = todayIso()
  filters.status = 'All Statuses'
  filters.search = ''
  page.value = 1
  loadPage()
}

function checkClass(value) {
  if (value === 'Clear') return 'bg-green-100 text-green-600'
  if (value === 'Conflict') return 'bg-red-100 text-red-600'
  return 'bg-amber-100 text-amber-600'
}

function statusClass(value) {
  if (value === 'Approved') return 'bg-green-100 text-green-600'
  if (value === 'Rejected') return 'bg-red-100 text-red-600'
  if (value === 'Cancelled') return 'bg-gray-100 text-gray-600'
  return 'bg-amber-100 text-amber-600'
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

onMounted(async () => {
  await loadMyContext()
  await loadDepartments()
  await loadPage()
})
</script>