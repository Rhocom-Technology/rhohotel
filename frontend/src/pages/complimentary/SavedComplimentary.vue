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
      <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Print Record</button>
      <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">Approve</button>
      <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Mark as Consumed</button>
    </div>

    <!-- Status Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Record Value</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Approved</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">₦25,000</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Benefit Type</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Dining</span>
        </div>
        <p class="text-xl font-bold text-gray-900 mt-1">Food Voucher</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Redemption Status</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Open</span>
        </div>
        <p class="text-xl font-bold text-gray-900 mt-1">Pending Use</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Linked Department</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Ready</span>
        </div>
        <p class="text-xl font-bold text-gray-900 mt-1">Restaurant</p>
      </div>
    </div>

    <!-- Details + Audit -->
    <div style="display:grid;grid-template-columns:1fr 340px;gap:12px;">

      <!-- Complimentary Details -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-5">Complimentary Details</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Complimentary Code</p>
            <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">CMP-000437</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Issue Date</p>
            <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">18 Apr 2026 • 03:24 PM</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Guest</p>
            <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">Ngozi Cole</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room</p>
            <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">511</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Complimentary Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">Food Voucher</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Value</p>
            <div class="px-3 py-2.5 text-xs font-bold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">₦25,000</div>
          </div>
        </div>

        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Reason / Justification</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg leading-relaxed min-h-16">
            Service recovery approval granted after delayed room readiness and guest wait time at check-in.
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Usage Rule</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg leading-relaxed">
            Redeemable once at restaurant POS against dinner items only.<br/>
            Cannot be exchanged for cash or combined with another voucher.
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Notes</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg leading-relaxed min-h-16">
            Guest has acknowledged the complimentary dinner voucher. Waiting for restaurant redemption confirmation.
          </div>
        </div>
      </div>

      <!-- Approval & Audit -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-4">
        <h3 class="text-sm font-bold text-gray-900">Approval & Audit</h3>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Approval Status</p>
          <div class="px-4 py-2.5 text-xs font-semibold text-green-700 bg-green-50 border border-green-200 rounded-lg">
            Approved • waiting consumption confirmation
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Approved By</p>
          <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">General Manager</div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Consumption Status</p>
          <div class="px-4 py-2.5 text-xs font-semibold text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-lg">
            Pending Use at restaurant POS
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Redemption Reference</p>
          <div class="px-3 py-2.5 text-xs text-gray-400 bg-gray-50 border border-gray-200 rounded-lg">Not yet posted</div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Audit Trail</p>
          <div class="bg-gray-50 rounded-xl border border-gray-200 px-4 py-3 space-y-3">
            <div v-for="a in audit" :key="a.time">
              <p class="text-xs font-semibold text-gray-900">{{ a.time }}</p>
              <p class="text-xs text-gray-500">{{ a.action }}</p>
            </div>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Related Actions</p>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <button class="px-4 py-2.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Edit Record</button>
            <button class="px-4 py-2.5 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel Record</button>
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


const audit = [
  { time: '18 Apr 2026 • 03:24 PM', action: 'Created by Front Desk Supervisor' },
  { time: '18 Apr 2026 • 03:41 PM', action: 'Approved by General Manager' },
  { time: '18 Apr 2026 • 04:05 PM', action: 'Notification sent to Restaurant outlet' },
]
</script>