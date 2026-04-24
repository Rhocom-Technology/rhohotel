<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:1200px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Stay Adjustment</h2>
            <p class="text-xs text-gray-400 mt-1">Enterprise automation for extending stay, recalculating charges, handling discount governance, and syncing guest access</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>

        <div class="px-8 py-6 space-y-5">

          <!-- Active Stay Summary -->
          <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4 flex items-start justify-between">
            <div>
              <p class="text-sm font-bold text-blue-700 mb-1">Active Stay Summary</p>
              <p class="text-xs text-blue-600 mb-3">OGUMBA WAYNE • Room 8408 • Executive Room • Current checkout 24 Feb 2026 12:00 • Current nights 3</p>
              <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">Balance Open</span>
            </div>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full flex-shrink-0">Eligible to Extend</span>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">

            <!-- Left: Adjustment Setup + Discount Setup -->
            <div class="space-y-5">
              <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
                <h3 class="text-sm font-bold text-gray-900 mb-4">Adjustment Setup</h3>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;" class="mb-4">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Current Check in</p>
                    <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">26 Feb 2026 12:00</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Current Nights</p>
                    <div class="px-3 py-2.5 text-xs font-bold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">5</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Current Expected Check-out</p>
                    <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">26 Feb 2026 12:00</div>
                  </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;" class="mb-4">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Room Rate</p>
                    <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">26 Feb 2026 12:00</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Adjustment Type</p>
                    <input type="text" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Reason for Adjustment</p>
                    <input type="text" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">New Check-out Date</p>
                    <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">26 Feb 2026 12:00</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">New Number of Nights</p>
                    <div class="px-3 py-2.5 text-xs font-bold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">Fixed Amount</div>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Difference</p>
                    <input type="text" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>
              </div>

              <div class="bg-white rounded-xl border border-gray-200 px-5 py-5">
                <h3 class="text-sm font-bold text-gray-900 mb-4">Discount Setup</h3>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Discount Type</p>
                    <select class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                      <option>Select</option>
                      <option>Percentage</option>
                      <option>Fixed Amount</option>
                      <option>Complimentary Night</option>
                    </select>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 mb-1.5">Discount for Adjusted Days</p>
                    <input type="text" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>
                <div>
                  <p class="text-xs text-gray-500 mb-1.5">Adjustment Notes</p>
                  <textarea rows="4"
                    placeholder="Add internal explanation, approval reference, or guest acknowledgement note"
                    class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
                </div>
              </div>
            </div>

            <!-- Right: Automation Impact -->
            <div class="space-y-4">
              <h3 class="text-sm font-bold text-gray-900">Automation Impact</h3>

              <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
                <p class="text-xs font-bold text-blue-700 mb-3">Financial Recalculation</p>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                  <div class="text-xs text-gray-600">Previous Nights: 3</div>
                  <div class="text-xs text-gray-600">New Nights: 5</div>
                  <div class="text-xs text-gray-600">Previous Total: ₦300,000</div>
                  <div class="text-xs font-bold text-gray-900">New Total: ₦500,000</div>
                </div>
              </div>

              <div class="bg-green-50 rounded-xl border border-green-200 px-5 py-4">
                <p class="text-xs font-bold text-green-700 mb-2">Keycard Automation</p>
                <p class="text-xs text-green-600 leading-relaxed">Keycard access will be extended automatically to the new checkout time. Regenerate card token if physical card refresh is required.</p>
              </div>

              <div class="bg-yellow-50 rounded-xl border border-yellow-200 px-5 py-4">
                <p class="text-xs font-bold text-yellow-700 mb-2">Approval Governance</p>
                <p class="text-xs text-yellow-600 leading-relaxed">Discount on extended days crosses policy threshold. Send manager approval request before finalizing if threshold enforcement is active.</p>
              </div>

              <div class="bg-blue-50 rounded-xl border border-blue-100 px-5 py-4">
                <p class="text-xs font-bold text-blue-700 mb-2">Guest Notification Trigger</p>
                <p class="text-xs text-blue-600 leading-relaxed">WhatsApp and email stay-extension confirmation can be sent automatically after approval.</p>
                <p class="text-xs text-blue-500 mt-1">Updated stay timeline will also sync to checkout workflow.</p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="$emit('close')">Cancel</button>
            <button class="px-5 py-2.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">Apply and Update Stay</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineEmits(['close'])
</script>