<template>
  <div class="bg-white rounded-xl border border-gray-200 px-6 py-10 text-center">
    <p v-if="loading" class="text-sm text-gray-500">Opening reservation details...</p>
    <div v-else>
      <p class="text-sm font-medium text-red-500">{{ errorMessage || 'Reservation not found.' }}</p>
      <button
        @click="router.push('/reservations')"
        class="mt-4 px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
      >
        Back to Reservations
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const errorMessage = ref('')

onMounted(async () => {
  const id = String(route.params.id || '').trim()
  if (!id) {
    loading.value = false
    errorMessage.value = 'Missing reservation id.'
    return
  }

  window.location.replace(`/app/hotel-room-reservation/${encodeURIComponent(id)}`)
})
</script>