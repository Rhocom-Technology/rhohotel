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
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Save Draft</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Submit Approval</button>
      </div>
    </div>

    <!-- Form Body -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:12px;">

      <!-- Left: Complimentary Details -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-5">Complimentary Details</h3>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Guest</p>
            <input v-model="form.guest" type="text" placeholder="Select existing guest"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room</p>
            <input v-model="form.room" type="text" placeholder="Auto-fill from guest or choose room"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Complimentary Type</p>
            <select v-model="form.type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>Food Voucher</option>
              <option>Airport Transfer</option>
              <option>Room Upgrade</option>
              <option>Amenity Basket</option>
              <option>Late Checkout</option>
              <option>Laundry</option>
              <option>Transport / Food</option>
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
            <p class="text-xs text-gray-500 mb-1.5">Value</p>
            <input v-model="form.value" type="text" placeholder="₦0.00"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Quantity / Limit</p>
            <input v-model="form.quantity" type="text" placeholder="1 unit / single use"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Issue Date</p>
            <input v-model="form.issueDate" type="text" placeholder="18 Apr 2026"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Expiry Date</p>
            <input v-model="form.expiryDate" type="text" placeholder="Select expiry / validity end"
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
          <textarea v-model="form.redemptionRule" rows="3"
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
          <select v-model="form.approvalLevel" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option>General Manager</option>
            <option>Duty Manager</option>
            <option>Front Desk Supervisor</option>
            <option>Operations Lead</option>
          </select>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Charge Impact</p>
          <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">
            Post to complimentary expense account
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Source Category</p>
          <select v-model="form.sourceCategory" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
            <option>Service Recovery</option>
            <option>VIP Courtesy</option>
            <option>Loyalty Reward</option>
            <option>Operational Adjustment</option>
          </select>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Usage Confirmation Required</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" checked class="accent-blue-600 w-3.5 h-3.5" />
              <span class="text-xs text-gray-700">Require outlet consumption confirmation</span>
            </label>
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" checked class="accent-blue-600 w-3.5 h-3.5" />
              <span class="text-xs text-gray-700">Notify front desk after redemption</span>
            </label>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Linked Actions</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" checked class="accent-blue-600 w-3.5 h-3.5" />
              <span class="text-xs text-gray-700">Notify guest by SMS / email</span>
            </label>
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" checked class="accent-blue-600 w-3.5 h-3.5" />
              <span class="text-xs text-gray-700">Notify linked outlet / department</span>
            </label>
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" checked class="accent-blue-600 w-3.5 h-3.5" />
              <span class="text-xs text-gray-700">Create audit trail entry</span>
            </label>
          </div>
        </div>

        <!-- Preview Summary -->
        <div>
          <p class="text-xs text-gray-500 mb-2">Preview Summary</p>
          <div class="bg-blue-50 rounded-xl border border-blue-200 px-4 py-4">
            <p class="text-xs font-bold text-blue-700 mb-2">{{ form.type }} • {{ form.department }}</p>
            <p class="text-xs text-blue-600">Guest: {{ form.guest || 'Select guest' }}</p>
            <p class="text-xs text-blue-600">Value: {{ form.value || '₦0.00' }}</p>
            <p class="text-xs text-blue-600">Approval: {{ form.approvalLevel }}</p>
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
import { reactive } from 'vue'

const form = reactive({
  guest: '',
  room: '',
  type: 'Food Voucher',
  department: 'Restaurant',
  value: '',
  quantity: '',
  issueDate: '18 Apr 2026',
  expiryDate: '',
  reason: '',
  redemptionRule: '',
  note: '',
  approvalLevel: 'General Manager',
  sourceCategory: 'Service Recovery',
})
</script>