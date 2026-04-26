<template>
  <SavedReservationDetail
    :reservation="reservation"
    :loading="reservationResource.loading"
    :error="errorMessage"
    :action-loading="actionLoading"
    @refresh="reload"
    @open-payments="router.push('/payments')"
    @check-in="checkInAllRooms"
    @cancel-reservation="cancelReservation"
    @create-invoice="createInvoice"
  />
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import SavedReservationDetail from '@/components/reservations/SavedReservation.vue'

const route = useRoute()
const router = useRouter()

const errorMessage = ref('')
const actionLoading = ref(false)

const reservationResource = createResource({
  url: 'frappe.client.get',
  params: {
    doctype: 'Hotel Front Desk Reservation',
    name: route.params.id,
  },
  auto: true,
  onError(error) {
    errorMessage.value = error?.messages?.[0] || 'Reservation not found.'
  },
})

const reservation = computed(() => reservationResource.data || {})

async function callApi(method, args = {}) {
  const response = await fetch('/api/method/' + method, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(args),
  })
  const payload = await response.json()
  if (!response.ok || payload.exc) {
    const msg = payload?._server_messages || payload?.message || 'Request failed'
    throw new Error(typeof msg === 'string' ? msg : 'Request failed')
  }
  return payload.message
}

function reload() {
  errorMessage.value = ''
  reservationResource.reload()
}

async function checkInAllRooms() {
  if (!reservation.value?.name) return
  actionLoading.value = true
  errorMessage.value = ''
  try {
    await callApi('rhohotel.rhocom_hotel.doctype.hotel_front_desk_reservation.hotel_front_desk_reservation.check_in_all_rooms', {
      reservation_name: reservation.value.name,
      check_in_notes: '',
    })
    reload()
  } catch (error) {
    errorMessage.value = String(error?.message || 'Could not check in rooms.')
  } finally {
    actionLoading.value = false
  }
}

async function cancelReservation() {
  if (!reservation.value?.name) return
  const confirmed = window.confirm(`Cancel reservation ${reservation.value.name}?`)
  if (!confirmed) return

  actionLoading.value = true
  errorMessage.value = ''
  try {
    await callApi('frappe.client.cancel', { doctype: 'Hotel Front Desk Reservation', name: reservation.value.name })
    router.push('/reservations')
  } catch (error) {
    errorMessage.value = String(error?.message || 'Could not cancel reservation.')
    actionLoading.value = false
  }
}

async function createInvoice() {
  if (!reservation.value?.name) return
  actionLoading.value = true
  errorMessage.value = ''
  try {
    await callApi('rhohotel.rhocom_hotel.doctype.hotel_front_desk_reservation.hotel_front_desk_reservation.create_sales_invoice_for_reservation', {
      reservation_name: reservation.value.name,
    })
    reload()
  } catch (error) {
    errorMessage.value = String(error?.message || 'Could not create invoice.')
  } finally {
    actionLoading.value = false
  }
}
</script>