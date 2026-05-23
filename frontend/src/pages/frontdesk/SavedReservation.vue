<template>
  <SavedReservationDetails
    :reservation="reservation"
    :loading="loading"
    :error="errorMessage"
    :action-loading="actionLoading"
    @refresh="loadReservation"
    @open-payments="openPayments"
    @check-in="goToCheckIn"
    @check-in-room="goToIndividualCheckIn"
    @bulk-check-in="goToBulkCheckIn"
    @update-occupant="saveRoomOccupant"
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

    const defaultGuest = doc.primary_guest_name || doc.customer || ''
    const rooms = Array.isArray(doc.rooms)
      ? doc.rooms.map((row) => ({
          ...row,
          occupant_name: row.occupant_name || row.guest_name || defaultGuest,
        }))
      : []

    reservation.value = {
      ...doc,
      status: doc.reservation_status || doc.status || 'Draft',
      rooms,
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

function goToIndividualCheckIn(row) {
  const id = getReservationId()
  const query = {}
  if (id) query.reservation = id
  if (row?.room_number) query.room = row.room_number
  if (row?.room_type) query.room_type = row.room_type

  const guestName = row?.occupant_name || row?.guest_name || reservation.value?.primary_guest_name || ''
  if (guestName) query.guest_name = guestName
  if (row?.hotel_guest) query.guest = row.hotel_guest
  if (row?.occupant_phone) query.guest_phone = row.occupant_phone
  if (row?.occupant_email) query.guest_email = row.occupant_email

  if (row?.number_of_nights) query.nights = row.number_of_nights
  if (reservation.value?.to_date) query.checkout_date = reservation.value.to_date

  // Discount — map reservation's discount_type/discount value
  const resDiscountType = reservation.value?.discount_type || 'None'
  if (resDiscountType && resDiscountType !== 'None') {
    query.discount_type = resDiscountType
    query.discount = reservation.value?.discount || 0
  }

  // Advance payments already received against this reservation
  const payments = Array.isArray(reservation.value?.payment_entries)
    ? reservation.value.payment_entries
    : []
  const advancePaid = payments.reduce((s, p) => s + (parseFloat(p.amount) || 0), 0)
  if (advancePaid > 0) query.advance_paid = advancePaid
  if (reservation.value?.sales_invoice) query.sales_invoice = reservation.value.sales_invoice

  router.push({ name: 'NewCheckIn', query })
}

function goToBulkCheckIn() {
  const id = getReservationId()
  router.push({ name: 'NewCheckIn', query: id ? { reservation: id } : undefined })
}

async function saveRoomOccupant(payload) {
  const row = payload?.row || payload
  const guest = payload?.guest || null
  if (!row?.name) {
    errorMessage.value = 'Could not save occupant: missing room row id.'
    return
  }

  actionLoading.value = true
  errorMessage.value = ''
  try {
    await callMethod('frappe.client.set_value', {
      doctype: 'Hotel Reservation Room',
      name: row.name,
      fieldname: 'occupant_name',
      value: row.occupant_name || row.guest_name || '',
    })

    if (guest?.phone_number) {
      await callMethod('frappe.client.set_value', {
        doctype: 'Hotel Reservation Room',
        name: row.name,
        fieldname: 'occupant_phone',
        value: guest.phone_number,
      })
    }

    if (guest?.email) {
      await callMethod('frappe.client.set_value', {
        doctype: 'Hotel Reservation Room',
        name: row.name,
        fieldname: 'occupant_email',
        value: guest.email,
      })
    }

    await loadReservation()
  } catch (error) {
    errorMessage.value = String(error?.message || 'Could not save room occupant.')
  } finally {
    actionLoading.value = false
  }
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
    await callMethod(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.cancel_reservation',
      { reservation_name: reservation.value.name },
    )
    await loadReservation()
  } catch (error) {
    errorMessage.value = String(error?.message || 'Could not cancel reservation.')
  } finally {
    actionLoading.value = false
  }
}

async function createInvoice() {
  if (!reservation.value?.name) return
  actionLoading.value = true
  errorMessage.value = ''
  try {
    await callMethod(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.create_invoice_for_reservation',
      { reservation_name: reservation.value.name },
    )
    await loadReservation()
  } catch (error) {
    errorMessage.value = String(error?.message || 'Could not create invoice.')
  } finally {
    actionLoading.value = false
  }
}

loadReservation()
</script>
