<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-y-auto" style="max-width:720px;max-height:92vh;">
        <div class="px-8 pt-8 pb-5 flex items-start justify-between border-b border-gray-100">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Print Reservation</h2>
            <p class="text-xs text-gray-400 mt-1">Print details for reservation {{ reservation.name }}</p>
          </div>
          <button @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm flex-shrink-0">✕</button>
        </div>
        <div class="px-8 py-6 space-y-5">
          <!-- Reservation details to print -->
          <div class="bg-gray-50 rounded-xl p-6">
            <h3 class="text-lg font-bold mb-2">Reservation Summary</h3>
            <p><span class="font-semibold">Guest:</span> {{ reservation.primary_guest_name || reservation.customer || '—' }}</p>
            <p><span class="font-semibold">Arrival:</span> {{ reservation.from_date }}</p>
            <p><span class="font-semibold">Departure:</span> {{ reservation.to_date }}</p>
            <p><span class="font-semibold">Nights:</span> {{ reservation.number_of_nights || 0 }}</p>
            <p><span class="font-semibold">Status:</span> {{ reservation.status || 'Draft' }}</p>
            <!-- Add more fields as needed -->
          </div>
          <div class="flex items-center justify-end gap-2 pt-2">
            <button class="px-5 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              @click="$emit('close')">Cancel</button>
            <button class="px-5 py-2.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              @click="handlePrint">Print</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
const props = defineProps({
  reservation: { type: Object, required: true }
})
const emit = defineEmits(['close', 'done'])

function handlePrint() {
  window.print()
  emit('done')
}
</script>
