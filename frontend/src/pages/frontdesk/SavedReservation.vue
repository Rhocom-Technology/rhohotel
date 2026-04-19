<template>
  <SavedReservationDetail
    :reservation="dummyReservation"
    @close="router.push('/reservations')"
  />
</template>

<script setup>
import { useRouter } from 'vue-router'
import SavedReservationDetail from '@/components/reservations/SavedReservation.vue'

const router = useRouter()

const dummyReservation = {
  name: 'RSV-2026-00418',
  reservation_type: 'Individual',
  primary_guest_name: 'OGUMBA WAYNE',
  customer: 'OGUMBA WAYNE',
  from_date: '2026-03-21',
  to_date: '2026-03-24',
  number_of_nights: 3,
  total_amount: 324000,
  subtotal: 120000,
  discount: 10,
  discount_amount: 36000,
  room_type: 'Executive Room',
  room_number: 'Pending assignment',
}
</script>