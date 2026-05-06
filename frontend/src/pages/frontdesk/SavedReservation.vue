<template>
  <SavedReservationDetails
    :reservation="reservation"
    :loading="loading"
    :error="errorMessage"
    :action-loading="actionLoading"
    @refresh="loadReservation"
    @open-payments="openPayments"
    @check-in="goToCheckIn"
    @cancel-reservation="cancelReservation"
    @create-invoice="createInvoice"
    @submit-reservation="submitReservation"
  />
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SavedReservationDetails from '@/components/reservations/SavedReservation.vue'
import { callMethod } from '@/lib/api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const actionLoading = ref(false)
const reservation = ref({})
const errorMessage = ref('')

function getReservationId() {
  return String(route.params.id || '').trim()
}

async function loadReservation() {
  const id = getReservationId()
  if (!id) {
    loading.value = false
    errorMessage.value = 'Missing reservation id.'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    const doc = await callMethod('frappe.client.get', {
      doctype: 'Hotel Reservation',
      name: id,
    })

    reservation.value = {
      ...doc,
      status: doc.reservation_status || doc.status || 'Draft',
      rooms: Array.isArray(doc.rooms) ? doc.rooms : [],
    }
  } catch (error) {
    reservation.value = {}
    errorMessage.value = String(error?.message || 'Could not load reservation details.')
  } finally {
    loading.value = false
  }
}

function openPayments() {
  const id = getReservationId()
  router.push({ name: 'Payments', query: id ? { reservation: id } : undefined })
}

function goToCheckIn() {
  const id = getReservationId()
  router.push({ name: 'NewCheckIn', query: id ? { reservation: id } : undefined })
}

async function submitReservation() {
  if (!reservation.value?.name || Number(reservation.value.docstatus) !== 0) return

  actionLoading.value = true
  errorMessage.value = ''
  try {
    const docToSubmit = {
      ...reservation.value,
      reservation_status: reservation.value?.reservation_status || reservation.value?.status || 'Confirmed',
    }

    if (docToSubmit.reservation_status === 'Draft' || docToSubmit.reservation_status === 'Hold') {
      docToSubmit.reservation_status = 'Confirmed'
    }

    await callMethod('frappe.client.submit', { doc: docToSubmit })
    await loadReservation()
  } catch (error) {
    errorMessage.value = String(error?.message || 'Could not submit reservation.')
  } finally {
    actionLoading.value = false
  }
}

async function cancelReservation() {
  if (!reservation.value?.name || Number(reservation.value.docstatus) === 2) return

  actionLoading.value = true
  errorMessage.value = ''
  try {
    await callMethod('frappe.client.cancel', { doc: reservation.value })
    await loadReservation()
  } catch (error) {
    errorMessage.value = String(error?.message || 'Could not cancel reservation.')
  } finally {
    actionLoading.value = false
  }
}

async function createInvoice() {
  errorMessage.value = 'Create Invoice is not available in this view yet.'
}

loadReservation()
</script>
