<template>
  <div class="space-y-5">

    <div>
      <h1 class="text-2xl font-bold text-gray-900">Saved Complimentary</h1>
      <p class="text-xs text-gray-400 mt-1">View the saved complimentary record, linked guest and room, approval status, value, issue rules, redemption details, and related actions.</p>
    </div>

    <!-- Action Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-end gap-2">
      <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        @click="$router.push('/complimentary/list')">Back to List</button>
      <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        @click="printRecord">Print Record</button>
      <button v-if="canEdit" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        @click="startEdit">Edit Record</button>
      <button v-if="canSubmit" class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors disabled:opacity-50"
        :disabled="submitResource.loading" @click="submitRecord">
        {{ submitResource.loading ? 'Submitting...' : 'Submit for Approval' }}
      </button>
      <button v-if="canApprove" class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors disabled:opacity-50"
        :disabled="approveResource.loading" @click="approveRecord">
        {{ approveResource.loading ? 'Approving...' : 'Approve' }}
      </button>
      <button v-if="canProgress" class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors disabled:opacity-50"
        :disabled="progressResource.loading" @click="markInProgress">
        {{ progressResource.loading ? 'Starting...' : 'Mark In Progress' }}
      </button>
      <button v-if="canConsume" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        :disabled="consumeResource.loading" @click="markConsumed">
        {{ consumeResource.loading ? 'Marking...' : 'Mark as Consumed' }}
      </button>
    </div>

    <!-- Feedback messages -->
    <div v-if="actionMsg" class="px-4 py-3 text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg">{{ actionMsg }}</div>
    <div v-if="errorMsg" class="px-4 py-3 text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg">{{ errorMsg }}</div>
    <div v-if="isLoading" class="px-4 py-3 text-xs text-gray-400">Loading...</div>

    <div v-if="showEdit && record" class="bg-white rounded-xl border border-blue-200 px-6 py-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-bold text-gray-900">Edit Complimentary</h3>
        <button class="text-xs text-gray-500 hover:text-gray-700" @click="showEdit = false">Close</button>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Guest</p>
          <input v-model="editForm.guest" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Room</p>
          <input v-model="editForm.room" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Type</p>
          <select v-model="editForm.complimentary_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg">
            <option>Food Voucher</option><option>Room Voucher</option><option>Airport Transfer</option><option>Room Upgrade</option><option>Amenity Basket</option><option>Late Checkout</option><option>Laundry</option><option>Transport / Food</option><option>Amenity / Late CO</option><option>Laundry / Amenity</option>
          </select>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Department</p>
          <select v-model="editForm.department" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg">
            <option>Restaurant</option><option>Front Desk</option><option>Housekeeping</option><option>Laundry</option><option>GM Office</option><option>Operations</option>
          </select>
        </div>
        <div v-if="editForm.complimentary_type === 'Room Upgrade'" class="col-span-2">
          <p class="text-xs text-gray-500 mb-1.5">Upgrade To Room <span class="text-red-500">*</span></p>
          <div v-if="loadingEditRooms" class="px-3 py-2.5 text-xs text-gray-400 border border-gray-200 rounded-lg bg-gray-50">Loading vacant rooms…</div>
          <select v-else v-model="editForm.upgrade_room" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">-- Select upgrade room --</option>
            <option v-for="r in editUpgradeRooms" :key="r.name" :value="r.name">
              Room {{ r.room_number || r.name }} — {{ r.room_type }}
            </option>
          </select>
          <p v-if="!editForm.upgrade_room" class="text-xs text-red-500 mt-1">Required: select the room to upgrade the guest into before approving.</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Value</p>
          <input v-model="editForm.value" type="number" min="0" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Approval Level</p>
          <select v-model="editForm.approval_level" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg">
            <option>General Manager</option><option>Duty Manager</option><option>Front Desk Supervisor</option><option>Operations Lead</option>
          </select>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Issue Date</p>
          <input v-model="editForm.issue_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Expiry Date</p>
          <input v-model="editForm.expiry_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg" />
        </div>
      </div>
      <div class="mt-3">
        <p class="text-xs text-gray-500 mb-1.5">Reason</p>
        <textarea v-model="editForm.reason" rows="2" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg"></textarea>
      </div>
      <div class="mt-3">
        <p class="text-xs text-gray-500 mb-1.5">Redemption Rule</p>
        <textarea v-model="editForm.redemption_rule" rows="2" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg"></textarea>
      </div>
      <div class="mt-3">
        <p class="text-xs text-gray-500 mb-1.5">Internal Note</p>
        <textarea v-model="editForm.note" rows="2" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg"></textarea>
      </div>
      <div class="flex justify-end gap-2 mt-4">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg" @click="showEdit = false">Cancel</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg disabled:opacity-50" :disabled="updateResource.loading" @click="saveEdit(false)">Save</button>
        <button v-if="record.status === 'Draft'" class="px-4 py-2 text-xs font-semibold text-white bg-green-600 rounded-lg disabled:opacity-50" :disabled="updateResource.loading" @click="saveEdit(true)">Save & Submit</button>
      </div>
    </div>

    <!-- Status Stats -->
    <div v-if="record" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Record Value</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="statusBadgeClass">{{ record.status }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ formatValue(record.value) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Benefit Type</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Benefit</span>
        </div>
        <p class="text-sm font-bold text-gray-900 mt-1">{{ record.complimentary_type }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Redemption Status</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">{{ record.status }}</span>
        </div>
        <p class="text-sm font-bold text-gray-900 mt-1">{{ record.status === 'Consumed' ? 'Consumed' : record.status === 'Approved' ? 'Pending Use' : record.status }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Linked Department</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Ready</span>
        </div>
        <p class="text-sm font-bold text-gray-900 mt-1">{{ record.department }}</p>
      </div>
    </div>

    <!-- Details + Audit -->
    <div v-if="record" style="display:grid;grid-template-columns:1fr 340px;gap:12px;">

      <!-- Complimentary Details -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-5">Complimentary Details</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Complimentary Code</p>
            <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ record.name }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Issue Date</p>
            <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ record.issue_date }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Guest</p>
            <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ record.guest }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room</p>
            <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ record.room || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Complimentary Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ record.complimentary_type }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Value</p>
            <div class="px-3 py-2.5 text-xs font-bold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ formatValue(record.value) }}</div>
          </div>
        </div>

        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Reason / Justification</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg leading-relaxed min-h-16">{{ record.reason || '—' }}</div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Usage Rule</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg leading-relaxed">{{ record.redemption_rule || '—' }}</div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Notes</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg leading-relaxed min-h-16">{{ record.note || '—' }}</div>
        </div>
      </div>

      <!-- Approval & Audit -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-4">
        <h3 class="text-sm font-bold text-gray-900">Approval & Audit</h3>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Approval Status</p>
          <div class="px-4 py-2.5 text-xs font-semibold rounded-lg border" :class="approvalStatusClass">
            {{ approvalStatusText }}
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Approved By</p>
          <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ record.approved_by || '—' }}</div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Consumption Status</p>
          <div class="px-4 py-2.5 text-xs font-semibold rounded-lg border" :class="consumptionStatusClass">
            {{ consumptionStatusText }}
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Redemption Reference</p>
          <div class="px-3 py-2.5 text-xs bg-gray-50 border border-gray-200 rounded-lg" :class="record.consumption_reference ? 'text-gray-900' : 'text-gray-400'">{{ record.consumption_reference || 'Not yet posted' }}</div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Audit Trail</p>
          <div class="bg-gray-50 rounded-xl border border-gray-200 px-4 py-3 space-y-3">
            <div v-if="!audit.length" class="text-xs text-gray-400">No audit entries yet.</div>
            <div v-for="a in audit" :key="a.time">
              <p class="text-xs font-semibold text-gray-900">{{ a.time }}</p>
              <p class="text-xs text-gray-500">{{ a.action }}</p>
            </div>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Related Actions</p>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <button v-if="canEdit" class="px-4 py-2.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors" @click="startEdit">Edit Record</button>
            <button v-if="canCancel" class="px-4 py-2.5 text-xs font-semibold text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
              :disabled="cancelResource.loading" @click="cancelRecord">
              {{ cancelResource.loading ? 'Cancelling...' : 'Cancel Record' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-3">
      <p class="text-xs text-gray-400">Saved complimentary record with detail, approval state, audit trail, and usage tracking.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { useSessionStore } from '@/stores/session'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

const record = ref(null)
const audit = ref([])
const errorMsg = ref('')
const actionMsg = ref('')
const showEdit = ref(false)
const editForm = ref({})
const editUpgradeRooms = ref([])
const loadingEditRooms = ref(false)

async function loadEditUpgradeRooms() {
  const checkIn = editForm.value?.check_in
  const currentRoom = editForm.value?.room || ''
  if (!checkIn) { editUpgradeRooms.value = []; return }
  loadingEditRooms.value = true
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.checkin.get_rooms_for_transfer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      body: new URLSearchParams({ current_room: currentRoom, check_in_dt: '', check_out_dt: '', exclude_reservation: '' }),
    })
    const data = await res.json()
    editUpgradeRooms.value = data.message || []
  } catch { editUpgradeRooms.value = [] } finally { loadingEditRooms.value = false }
}

// ── Fetch record ──────────────────────────────────────────────────────────────
const fetchResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.get_complimentary',
  onSuccess(data) {
    record.value = data
    audit.value = data.audit_trail || []
  },
  onError(err) {
    errorMsg.value = err?.message || 'Failed to load record'
  },
})

function loadRecord() {
  fetchResource.fetch({ complimentary_name: route.params.id })
}

const updateResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.update_complimentary',
  onSuccess(res) {
    if (res.success) {
      actionMsg.value = res.status === 'Pending' ? 'Record saved and submitted for approval.' : 'Record updated.'
      showEdit.value = false
      loadRecord()
    } else {
      errorMsg.value = res.error || 'Update failed'
    }
  },
  onError(err) { errorMsg.value = err?.message || 'Update failed' },
})

const submitResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.submit_complimentary',
  onSuccess(res) {
    if (res.success) {
      actionMsg.value = 'Submitted for approval.'
      loadRecord()
    } else {
      errorMsg.value = res.error || 'Submit failed'
    }
  },
  onError(err) { errorMsg.value = err?.message || 'Submit failed' },
})

const progressResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.mark_in_progress',
  onSuccess(res) {
    if (res.success) {
      actionMsg.value = 'Marked as in progress.'
      loadRecord()
    } else {
      errorMsg.value = res.error || 'Failed to mark in progress'
    }
  },
  onError(err) { errorMsg.value = err?.message || 'Failed to mark in progress' },
})

// ── Approve ───────────────────────────────────────────────────────────────────
const approveResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.approve_complimentary',
  onSuccess(res) {
    if (res.success) {
      actionMsg.value = 'Record approved successfully.'
      loadRecord()
    } else {
      errorMsg.value = res.error || 'Approval failed'
    }
  },
  onError(err) { errorMsg.value = err?.message || 'Approval failed' },
})

// ── Mark Consumed ─────────────────────────────────────────────────────────────
const consumeResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.mark_consumed',
  onSuccess(res) {
    if (res.success) {
      actionMsg.value = 'Marked as consumed.'
      loadRecord()
    } else {
      errorMsg.value = res.error || 'Failed to mark consumed'
    }
  },
  onError(err) { errorMsg.value = err?.message || 'Failed to mark consumed' },
})

// ── Cancel ────────────────────────────────────────────────────────────────────
const cancelResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.cancel_complimentary',
  onSuccess(res) {
    if (res.success) {
      router.push('/complimentary/list')
    } else {
      errorMsg.value = res.error || 'Cancellation failed'
    }
  },
  onError(err) { errorMsg.value = err?.message || 'Cancellation failed' },
})

// ── Actions ───────────────────────────────────────────────────────────────────
function approveRecord() {
  errorMsg.value = ''
  actionMsg.value = ''
  approveResource.fetch({ complimentary_name: route.params.id })
}

function markInProgress() {
  errorMsg.value = ''
  actionMsg.value = ''
  progressResource.fetch({ complimentary_name: route.params.id })
}

function markConsumed() {
  errorMsg.value = ''
  actionMsg.value = ''
  const consumptionReference = window.prompt('Enter outlet/POS/reference number for this consumption')
  if (!consumptionReference || !consumptionReference.trim()) {
    errorMsg.value = 'Consumption reference is required.'
    return
  }
  consumeResource.fetch({ complimentary_name: route.params.id, consumption_reference: consumptionReference.trim() })
}

function cancelRecord() {
  errorMsg.value = ''
  actionMsg.value = ''
  cancelResource.fetch({ complimentary_name: route.params.id })
}

function printRecord() {
  window.print()
}

function startEdit() {
  if (!record.value) return
  editForm.value = {
    guest: record.value.guest || '',
    room: record.value.room || '',
    reservation: record.value.reservation || null,
    check_in: record.value.check_in || null,
    complimentary_type: record.value.complimentary_type || 'Food Voucher',
    department: record.value.department || 'Restaurant',
    value: record.value.value || 0,
    quantity: record.value.quantity || '1',
    issue_date: record.value.issue_date || '',
    expiry_date: record.value.expiry_date || '',
    reason: record.value.reason || '',
    redemption_rule: record.value.redemption_rule || '',
    note: record.value.note || '',
    approval_level: record.value.approval_level || 'General Manager',
    source_category: record.value.source_category || 'Service Recovery',
    upgrade_room: record.value.upgrade_room || '',
    late_checkout_time: record.value.late_checkout_time || '',
  }
  if (record.value.complimentary_type === 'Room Upgrade') loadEditUpgradeRooms()
  showEdit.value = true
}

function saveEdit(submitForApproval) {
  errorMsg.value = ''
  actionMsg.value = ''
  updateResource.fetch({
    complimentary_name: route.params.id,
    complimentary_data: editForm.value,
    submit_for_approval: submitForApproval ? 1 : 0,
  })
}

// ── Computed display helpers ──────────────────────────────────────────────────
const statusBadgeClass = computed(() => {
  const s = record.value?.status
  return {
    'Draft':       'bg-gray-100 text-gray-500',
    'Approved':    'bg-green-100 text-green-600',
    'In Progress': 'bg-blue-100 text-blue-600',
    'Consumed':    'bg-green-100 text-green-700',
    'Pending':     'bg-yellow-100 text-yellow-600',
    'Expired':     'bg-gray-100 text-gray-500',
    'Cancelled':   'bg-red-100 text-red-500',
  }[s] || 'bg-gray-100 text-gray-500'
})

function formatValue(v) {
  if (!v && v !== 0) return '—'
  return '₦' + Number(v).toLocaleString()
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const approvalStatusText = computed(() => {
  const s = record.value?.status
  if (s === 'Draft') return 'Draft • not submitted'
  if (s === 'Approved') return 'Approved • waiting consumption confirmation'
  if (s === 'Consumed') return 'Consumed and closed'
  if (s === 'Cancelled') return 'Cancelled'
  if (s === 'Pending') return 'Pending approval'
  return s || '—'
})

const approvalStatusClass = computed(() => {
  const s = record.value?.status
  if (s === 'Approved') return 'text-green-700 bg-green-50 border-green-200'
  if (s === 'Consumed') return 'text-green-700 bg-green-50 border-green-200'
  if (s === 'Cancelled') return 'text-red-700 bg-red-50 border-red-200'
  return 'text-yellow-700 bg-yellow-50 border-yellow-200'
})

const consumptionStatusClass = computed(() => {
  const s = record.value?.status
  if (s === 'Consumed') return 'text-green-700 bg-green-50 border-green-200'
  if (s === 'Cancelled' || s === 'Expired') return 'text-gray-700 bg-gray-50 border-gray-200'
  return 'text-yellow-700 bg-yellow-50 border-yellow-200'
})

const consumptionStatusText = computed(() => {
  const s = record.value?.status
  if (s === 'Consumed') return `Consumed on ${formatDate(record.value?.consumed_on)}`
  if (s === 'Cancelled') return 'Cancelled — benefit not used'
  if (s === 'Expired') return 'Expired — benefit unused'
  const dept = record.value?.department || 'outlet'
  return `Pending use at ${dept}`
})

const isLoading = computed(() => fetchResource.loading)
const canEdit = computed(() => ['Draft', 'Pending'].includes(record.value?.status))
const canSubmit = computed(() => record.value?.status === 'Draft')
const canApprove = computed(() => record.value?.status === 'Pending' && session.hasAnyRole(['System Manager', 'Hotel Manager', 'Front Desk Manager']))
const canProgress = computed(() => record.value?.status === 'Approved')
const canConsume = computed(() => ['Approved', 'In Progress'].includes(record.value?.status))
const canCancel  = computed(() => !['Consumed', 'Cancelled', 'Expired'].includes(record.value?.status))

onMounted(loadRecord)
</script>
