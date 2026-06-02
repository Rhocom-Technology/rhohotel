<template>
  <div class="space-y-5">

    <!-- Breadcrumb -->
    <div class="text-xs text-gray-400">
      Operations / <span class="text-gray-600 cursor-pointer hover:underline" @click="$router.push('/complimentary')">Complimentary Management</span> / <span class="text-gray-600">New Complimentary</span>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">New Complimentary</h1>
      <p class="text-xs text-gray-400 mt-1">Create a new complimentary record for a guest, define the benefit, approval route, value impact, validity, and redemption conditions.</p>
    </div>

    <!-- Action Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Create Complimentary Record</h3>
        <p class="text-xs text-gray-400 mt-0.5">Use this form to issue guest goodwill benefits, service recovery offers, loyalty rewards, or operational complimentary items.</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/complimentary/list')">Cancel</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          :disabled="submitResource.loading" @click="saveDraft">Save Draft</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          :disabled="submitResource.loading" @click="submitApproval">
          {{ submitResource.loading ? 'Submitting...' : 'Submit Approval' }}
        </button>
      </div>
    </div>

    <!-- Form Body -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:12px;">

      <!-- Left: Complimentary Details -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-5">Complimentary Details</h3>

        <!-- Error message -->
        <div v-if="errorMsg" class="mb-4 px-4 py-3 text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg">{{ errorMsg }}</div>

        <!-- Guest selector from active check-ins -->
        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Select Active Guest</p>
          <select v-model="selectedCheckIn" @change="onCheckinSelect" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option value="">-- Select checked-in guest --</option>
            <option v-for="c in checkins" :key="c.check_in" :value="c.check_in">
              {{ c.guest }} — Room {{ c.room_number }}
            </option>
          </select>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Guest</p>
            <input v-model="form.guest" type="text" placeholder="Guest name"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room</p>
            <input v-model="form.room" type="text" placeholder="Room number"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Complimentary Type</p>
            <select v-model="form.complimentary_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>Food Voucher</option>
              <option>Airport Transfer</option>
              <option>Room Upgrade</option>
              <option>Amenity Basket</option>
              <option>Late Checkout</option>
              <option>Laundry</option>
              <option>Transport / Food</option>
              <option>Amenity / Late CO</option>
              <option>Laundry / Amenity</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Department</p>
            <select v-model="form.department" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>Restaurant</option>
              <option>Front Desk</option>
              <option>Housekeeping</option>
              <option>GM Office</option>
              <option>Operations</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Value (₦)</p>
            <input v-model="form.value" type="text" placeholder="0.00"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Quantity / Limit</p>
            <input v-model="form.quantity" type="text" placeholder="1 unit / single use"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Issue Date</p>
            <input v-model="form.issue_date" type="date"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Expiry Date</p>
            <input v-model="form.expiry_date" type="date"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Reason / Justification</p>
          <textarea v-model="form.reason" rows="3"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="Explain why this complimentary is being issued: service recovery, VIP courtesy, loyalty reward, operational adjustment..."></textarea>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Redemption Rule</p>
          <textarea v-model="form.redemption_rule" rows="3"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="Define how this benefit can be used, where it can be redeemed, limits, and whether cash exchange is prohibited..."></textarea>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Internal Note</p>
          <textarea v-model="form.note" rows="3"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="Internal approval notes, outlet communication, or supporting context..."></textarea>
        </div>
      </div>

      <!-- Right: Approval & Control -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-4">
        <h3 class="text-sm font-bold text-gray-900">Approval & Control</h3>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Approval Level</p>
          <select v-model="form.approval_level" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option>General Manager</option>
            <option>Duty Manager</option>
            <option>Front Desk Supervisor</option>
            <option>Operations Lead</option>
          </select>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Charge Impact</p>
          <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">
            Track approved value for complimentary reporting
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Source Category</p>
          <select v-model="form.source_category" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option>Service Recovery</option>
            <option>VIP Courtesy</option>
            <option>Loyalty Reward</option>
            <option>Operational Adjustment</option>
          </select>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Usage Confirmation Required</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
            <p class="text-xs text-gray-700">Approved items must be marked consumed with a reference by the responsible department.</p>
            <p class="text-xs text-gray-500">Every approval, consumption, and cancellation is recorded on the complimentary record.</p>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Operational Routing</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
            <p class="text-xs text-gray-700">Department: {{ form.department }}</p>
            <p class="text-xs text-gray-700">Approval queue: {{ form.approval_level }}</p>
            <p class="text-xs text-gray-500">Drafts can be edited before submission.</p>
          </div>
        </div>

        <!-- Preview Summary -->
        <div>
          <p class="text-xs text-gray-500 mb-2">Preview Summary</p>
          <div class="bg-blue-50 rounded-xl border border-blue-200 px-4 py-4">
            <p class="text-xs font-bold text-blue-700 mb-2">{{ form.complimentary_type }} • {{ form.department }}</p>
            <p class="text-xs text-blue-600">Guest: {{ form.guest || 'Select guest' }}</p>
            <p class="text-xs text-blue-600">Value: {{ form.value ? '₦' + form.value : '₦0.00' }}</p>
            <p class="text-xs text-blue-600">Approval: {{ form.approval_level }}</p>
          </div>
        </div>

        <!-- Quick Tips -->
        <div>
          <p class="text-xs text-gray-500 mb-2">Quick Tips</p>
          <div class="bg-gray-50 rounded-xl border border-gray-200 px-4 py-3">
            <p class="text-xs text-gray-500">Use clear reason and outlet rule to avoid misuse.</p>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const errorMsg = ref('')
const successMsg = ref('')

const form = reactive({
  guest: '',
  room: '',
  reservation: '',
  check_in: '',
  complimentary_type: 'Food Voucher',
  department: 'Restaurant',
  value: '',
  quantity: '1',
  issue_date: new Date().toISOString().slice(0, 10),
  expiry_date: '',
  reason: '',
  redemption_rule: '',
  note: '',
  approval_level: 'General Manager',
  source_category: 'Service Recovery',
})

// ── Active check-ins for guest/room dropdowns ─────────────────────────────────
const checkins = ref([])
const selectedCheckIn = ref('')

const checkinsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.get_active_checkins',
  onSuccess(data) {
    checkins.value = data.checkins || []
  },
})

function onCheckinSelect() {
  const selected = checkins.value.find(c => c.check_in === selectedCheckIn.value)
  if (selected) {
    form.check_in = selected.check_in
    form.reservation = selected.reservation || ''
    form.guest = selected.guest
    form.room = selected.room_number
  } else {
    form.check_in = ''
    form.reservation = ''
  }
}

// ── Validation ────────────────────────────────────────────────────────────────
const validationErrors = computed(() => {
  const errors = []
  if (!form.guest.trim()) errors.push('Guest name is required')
  if (!form.complimentary_type) errors.push('Complimentary type is required')
  if (!form.department) errors.push('Department is required')
  if (!form.approval_level) errors.push('Approval level is required')
  if (!form.issue_date) errors.push('Issue date is required')
  return errors
})

// ── Create ────────────────────────────────────────────────────────────────────
const submitResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.complimentary.create_complimentary',
  onSuccess(res) {
    if (res.success) {
      successMsg.value = `Created: ${res.complimentary_name}`
      router.push('/complimentary/' + res.complimentary_name)
    } else {
      errorMsg.value = res.error || 'Failed to create record'
    }
  },
  onError(err) {
    errorMsg.value = err?.message || 'An error occurred'
  },
})

function payload() {
  return {
    guest: form.guest,
    room: form.room,
    reservation: form.reservation || null,
    check_in: form.check_in || null,
    complimentary_type: form.complimentary_type,
    department: form.department,
    value: form.value ? parseFloat(String(form.value).replace(/[^0-9.]/g, '')) : 0,
    quantity: form.quantity,
    issue_date: form.issue_date,
    expiry_date: form.expiry_date || null,
    reason: form.reason,
    redemption_rule: form.redemption_rule,
    note: form.note,
    approval_level: form.approval_level,
    source_category: form.source_category,
  }
}

function submitRecord(submitForApproval) {
  errorMsg.value = ''
  if (validationErrors.value.length) {
    errorMsg.value = validationErrors.value[0]
    return
  }
  submitResource.fetch({
    complimentary_data: payload(),
    submit_for_approval: submitForApproval ? 1 : 0,
  })
}

function submitApproval() {
  submitRecord(true)
}

function saveDraft() {
  submitRecord(false)
}

onMounted(() => {
  checkinsResource.fetch()
})
</script>
