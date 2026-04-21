<template>
  <NewReservationForm
    :type="type"
    @close="router.push('/reservations')"
    @saved="onSaved"
  />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import NewReservationForm from '@/components/reservations/NewReservationForm.vue'

const route = useRoute()
const router = useRouter()
const type = computed(() => route.query.type || 'Individual')

function onSaved(doc) {
  const name = doc?.name
  if (!name) {
    router.push('/reservations')
    return
  }
  router.push({ name: 'SavedReservation', params: { id: name } })
}
</script>