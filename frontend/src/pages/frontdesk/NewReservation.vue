<template>
  <NewReservationForm
    :type="type"
    @close="router.push('/reservations')"
    @saved="router.push('/reservations')"
  />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import NewReservationForm from '@/components/reservations/NewReservationForm.vue'

const route = useRoute()
const router = useRouter()
const type = computed(() => route.query.type || 'Individual')
</script>