<template>
  <div class="space-y-0">
    <AIInsightPanel
      v-if="reservation?.name"
      title="AI Reservation Review"
      context-type="reservation_quality_review"
      :context-data="reservationAiContext"
      :auto-load="false"
      panel-id="saved-reservation-review"
      style="margin-bottom:8px;"
    />
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
    @update-room-discount="saveRoomDiscount"
    @distribute-room-discount="distributeRoomDiscount"
    @cancel-reservation="cancelReservation"
    @create-invoice="createInvoice"
    @submit-reservation="submitReservation"
    @edit-draft="editDraft"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SavedReservationDetails from '@/components/reservations/SavedReservation.vue'
import { callMethod } from '@/lib/api'
import AIInsightPanel from '@/components/ai/AIInsightPanel.vue'

// Utility: Check if a guest exists by name or id
async function ensureGroupMasterPayerExists(payerName, payerDetails = {}) {
  if (!payerName) return null;
  // Try to get the guest by name
  try {
    const guest = await callMethod('frappe.client.get_value', {
      doctype: 'Hotel Guest',
      filters: { guest_name: payerName },
      fieldname: ['name'],
    });
    if (guest && guest.name) {
      return guest.name;
    }
  } catch (e) {
    // Not found, will create
  }
  // Create new guest
  try {
    const newGuest = await callMethod('frappe.client.insert', {
      doc: {
        doctype: 'Hotel Guest',
        guest_name: payerName,
        ...payerDetails,
      },
    });
    return newGuest.name;
  } catch (e) {
    throw new Error('Could not create group master payer: ' + (e?.message || e));
  }
}

// Utility: Update reservation with group master payer
async function updateReservationGroupMaster(reservationName, groupMasterName) {
  if (!reservationName || !groupMasterName) return;
  await callMethod('frappe.client.set_value', {
    doctype: 'Hotel Reservation',
    name: reservationName,
    fieldname: 'group_master_customer',
    value: groupMasterName,
  });
}

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const actionLoading = ref(false)
const reservation = ref({})
const errorMessage = ref('')

function toUserError(error, fallback) {
  const raw = String(error?.message || '').trim()
  if (!raw) return fallback

  const technicalPattern = /traceback|frappe\.|pymysql|sql|exception|line\s+\d+|doctype|\n/i
  if (raw.length > 220 || technicalPattern.test(raw)) {
    return fallback
  }
  return raw
}

function getPaymentValue(entry) {
  return Number(entry?.amount ?? entry?.paid_amount ?? entry?.allocated_amount ?? 0)
}

function normalizeInvoiceRow(row) {
  return {
    name: row?.invoice || row?.name || '',
    invoice_type: row?.invoice_type || (Number(row?.is_return || 0) ? 'Credit Note' : 'Invoice'),
    posting_date: row?.posting_date || null,
    grand_total: Number(row?.amount ?? row?.grand_total ?? 0),
    outstanding_amount: Number(row?.outstanding_amount ?? 0),
    status: row?.status || '',
    is_return: Number(row?.is_return || 0),
    room_row: row?.room_row || row?.room_row_name || '',
    room_number: row?.room_number || '',
    invoice_scope: row?.invoice_scope || '',
  }
}

function normalizePaymentRow(row) {
  return {
    name: row?.payment_entry || row?.name || '',
    posting_date: row?.posting_date || null,
    mode_of_payment: row?.mode_of_payment || '',
    reference_no: row?.reference_no || '',
    remarks: row?.remarks || '',
    amount: getPaymentValue(row),
  }
}

function getReservationId() {
  return String(route.params.id || '').trim()
}

function isReservationCancelled() {
  return Number(reservation.value?.docstatus || 0) === 2
    || String(reservation.value?.status || reservation.value?.reservation_status || '').toLowerCase() === 'cancelled'
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
    const paymentSummary = await callMethod(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.get_payment_summary_for_reservation',
      { reservation_name: id },
    ).catch(() => null)

    const defaultGuest = doc.primary_guest_name || doc.customer || ''
    const rooms = Array.isArray(doc.rooms)
      ? doc.rooms.map((row) => ({
          ...row,
          occupant_name: row.occupant_name || row.guest_name || defaultGuest,
        }))
      : []

    const reservationInvoices = (Array.isArray(doc.reservation_invoices) ? doc.reservation_invoices : [])
      .map(normalizeInvoiceRow)
    const fallbackInvoices = (Array.isArray(paymentSummary?.invoices) ? paymentSummary.invoices : [])
      .map(normalizeInvoiceRow)
    const invoiceEntries = fallbackInvoices.length ? fallbackInvoices : reservationInvoices

    const reservationPayments = (Array.isArray(doc.reservation_payments) ? doc.reservation_payments : [])
      .map(normalizePaymentRow)
    const fallbackPayments = (Array.isArray(paymentSummary?.payment_entries) ? paymentSummary.payment_entries : [])
      .map(normalizePaymentRow)
    const paymentEntries = fallbackPayments.length ? fallbackPayments : reservationPayments

    const fallbackPaidAmount = paymentEntries.reduce((sum, row) => sum + getPaymentValue(row), 0)
    const paidAmount = Number(paymentSummary?.paid_amount ?? fallbackPaidAmount)
    const totalAmount = parseFloat(doc.total_amount || doc.net_total || 0)
    const outstandingAmount = Number(paymentSummary?.outstanding_amount)
    const balanceAmount = Number.isFinite(outstandingAmount)
      ? Math.max(0, outstandingAmount)
      : Math.max(0, totalAmount - paidAmount)

    reservation.value = {
      ...doc,
      status: doc.reservation_status || doc.status || 'Draft',
      rooms,
      paid_amount: paidAmount,
      balance: Number(paymentSummary?.balance ?? balanceAmount),
      payment_entries: paymentEntries,
      reservation_invoices: invoiceEntries,
      reservation_payments: paymentEntries,
      linked_invoices: invoiceEntries,
    }
  } catch (error) {
    reservation.value = {}
    errorMessage.value = toUserError(error, 'Could not load reservation details.')
  } finally {
    loading.value = false
  }
}

function openPayments() {
  const id = getReservationId()
  router.push({ name: 'Payments', query: id ? { reservation: id } : undefined })
}

function goToCheckIn() {
  if (isReservationCancelled()) return
  const id = getReservationId()
  const res = reservation.value
  const rooms = Array.isArray(res?.rooms) ? res.rooms : []
  const pendingRooms = rooms.filter(r => !r.check_in_reference)

  if (!pendingRooms.length) {
    errorMessage.value = 'All reservation rooms are already checked in.'
    return
  }

  // For corporate/group reservations, force explicit room/occupant selection.
  if (res?.reservation_type === 'Corporate' || res?.reservation_type === 'Group') {
    if (pendingRooms.length === 1) {
      goToIndividualCheckIn(pendingRooms[0])
      return
    }

    if (typeof window !== 'undefined') {
      const options = pendingRooms
        .map((room, index) => `${index + 1}. ${room.room_number || 'Unassigned room'} - ${room.occupant_name || room.guest_name || 'No occupant'}`)
        .join('\n')
      const selected = window.prompt(`Select room to check in by number:\n${options}`)
      const selectedIndex = Number(selected) - 1
      if (!Number.isInteger(selectedIndex) || selectedIndex < 0 || selectedIndex >= pendingRooms.length) {
        return
      }
      goToIndividualCheckIn(pendingRooms[selectedIndex])
      return
    }
  }

  const firstRoom = pendingRooms[0]

  const query = {}
  if (id) query.reservation = id
  if (id) query.canonical_reservation = id
  if (res?.reservation_type) query.reservation_type = res.reservation_type
  if (firstRoom?.room_number) query.room = firstRoom.room_number
  if (firstRoom?.room_type) query.room_type = firstRoom.room_type
  if (firstRoom?.rate_per_night) query.rate_amount = firstRoom.rate_per_night

  const guestName = firstRoom?.occupant_name || firstRoom?.guest_name || res?.primary_guest_name || res?.customer || ''
  if (guestName) query.guest_name = guestName
  const guestId = firstRoom?.hotel_guest || res?.hotel_guest || ((res?.reservation_type === 'Corporate') ? res?.corporate_guest : '')
  if (guestId) query.guest = guestId
  if (firstRoom?.occupant_phone || res?.primary_guest_phone) query.guest_phone = firstRoom.occupant_phone || res.primary_guest_phone
  if (firstRoom?.occupant_email || res?.primary_guest_email) query.guest_email = firstRoom.occupant_email || res.primary_guest_email
  if (res?.corporate_guest) query.corporate_guest = res.corporate_guest
  if (res?.customer) query.customer = res.customer
  if (res?.group_billing_mode) query.group_billing_mode = res.group_billing_mode
  if (res?.group_master_customer) query.group_master_customer = res.group_master_customer

  const nights = firstRoom?.number_of_nights || res?.number_of_nights
  if (nights) query.nights = nights
  if (res?.from_date) query.check_in_dt = `${res.from_date} 14:00:00`
  if (res?.to_date) query.checkout_date = res.to_date

  const resDiscountType = res?.discount_type || 'None'
  if (resDiscountType && resDiscountType !== 'None') {
    query.discount_type = resDiscountType
    query.discount = res?.discount || 0
  }

  const payments = Array.isArray(res?.payment_entries) ? res.payment_entries : []
  const advancePaid = payments.reduce((sum, payment) => sum + getPaymentValue(payment), 0)
  if (advancePaid > 0) query.advance_paid = advancePaid
  if (res?.sales_invoice) query.sales_invoice = res.sales_invoice

  router.push({ name: 'NewCheckIn', query })
}

function goToIndividualCheckIn(row) {
  const id = getReservationId()
  const query = {}
  if (id) query.reservation = id
  if (id) query.canonical_reservation = id
  if (reservation.value?.reservation_type) query.reservation_type = reservation.value.reservation_type
  if (row?.check_in_reference) {
    errorMessage.value = `${row.room_number || 'This room'} is already checked in.`
    return
  }

  if (row?.room_number) query.room = row.room_number
  if (row?.room_type) query.room_type = row.room_type
  if (row?.rate_per_night) query.rate_amount = row.rate_per_night

  const guestName = row?.occupant_name || row?.guest_name || reservation.value?.primary_guest_name || ''
  if (guestName) query.guest_name = guestName
  const fallbackCorporateGuest = reservation.value?.reservation_type === 'Corporate'
    ? reservation.value?.corporate_guest
    : ''
  if (row?.hotel_guest || fallbackCorporateGuest) query.guest = row.hotel_guest || fallbackCorporateGuest
  if (row?.occupant_phone || reservation.value?.primary_guest_phone) query.guest_phone = row.occupant_phone || reservation.value.primary_guest_phone
  if (row?.occupant_email || reservation.value?.primary_guest_email) query.guest_email = row.occupant_email || reservation.value.primary_guest_email
  if (reservation.value?.corporate_guest) query.corporate_guest = reservation.value.corporate_guest
  if (reservation.value?.customer) query.customer = reservation.value.customer

  if (row?.number_of_nights) query.nights = row.number_of_nights
  if (reservation.value?.from_date) query.check_in_dt = `${reservation.value.from_date} 14:00:00`
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
  const advancePaid = payments.reduce((sum, payment) => sum + getPaymentValue(payment), 0)
  if (advancePaid > 0) query.advance_paid = advancePaid
  if (reservation.value?.sales_invoice) query.sales_invoice = reservation.value.sales_invoice

  router.push({ name: 'NewCheckIn', query })
}

function goToBulkCheckIn() {
  if (isReservationCancelled()) return
  const id = getReservationId()
  router.push({ name: 'NewCheckIn', query: id ? { reservation: id, canonical_reservation: id } : undefined })
}

async function saveRoomOccupant(payload) {
  if (isReservationCancelled()) {
    errorMessage.value = 'Cancelled reservations cannot be edited.'
    return
  }
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
    errorMessage.value = toUserError(error, 'Could not save room occupant.')
  } finally {
    actionLoading.value = false
  }
}

async function saveRoomDiscount(payload) {
  if (isReservationCancelled()) {
    errorMessage.value = 'Cancelled reservations cannot be edited.'
    return
  }
  const row = payload?.row || payload
  if (!row?.name) {
    errorMessage.value = 'Could not save discount: missing room row id.'
    return
  }

  actionLoading.value = true
  errorMessage.value = ''
  try {
    await callMethod(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.apply_split_room_discount',
      {
        reservation_name: reservation.value.name,
        room_row_name: row.name,
        discount: Number(row.discount || 0),
        reason: 'Front desk split room discount',
      },
    )
    await loadReservation()
  } catch (error) {
    errorMessage.value = toUserError(error, 'Could not save room discount.')
  } finally {
    actionLoading.value = false
  }
}

async function distributeRoomDiscount(payload) {
  if (isReservationCancelled()) {
    errorMessage.value = 'Cancelled reservations cannot be edited.'
    return
  }
  if (!reservation.value?.name) return

  actionLoading.value = true
  errorMessage.value = ''
  try {
    await callMethod(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.distribute_split_room_discount',
      {
        reservation_name: reservation.value.name,
        discount: Number(payload?.discount || 0),
        discount_type: payload?.discount_type || 'Fixed Amount',
        room_row_names: payload?.room_row_names || [],
        reason: 'Front desk split discount distribution',
      },
    )
    await loadReservation()
  } catch (error) {
    errorMessage.value = toUserError(error, 'Could not distribute room discount.')
  } finally {
    actionLoading.value = false
  }
}

async function submitReservation() {
  if (isReservationCancelled()) return
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
    errorMessage.value = toUserError(error, 'Could not submit reservation.')
  } finally {
    actionLoading.value = false
  }
}

function editDraft() {
  const id = getReservationId()
  if (!id) return
  router.push({ name: 'NewReservation', query: { draft: id } })
}

async function cancelReservation() {
  if (!reservation.value?.name || Number(reservation.value.docstatus) === 2) return

  // Show confirmation dialog before proceeding
  if (typeof window !== 'undefined') {
    const confirmed = window.confirm('Are you sure you want to cancel this reservation? This action cannot be undone.')
    if (!confirmed) return
  }

  actionLoading.value = true
  errorMessage.value = ''
  try {
    await callMethod(
      'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.cancel_reservation',
      { reservation_name: reservation.value.name },
    )
    await loadReservation()
  } catch (error) {
    errorMessage.value = toUserError(error, 'Could not cancel reservation.')
  } finally {
    actionLoading.value = false
  }
}

async function createInvoice() {
  if (isReservationCancelled()) {
    errorMessage.value = 'Cancelled reservations cannot be edited.'
    return
  }
  if (!reservation.value?.name) return

  const reservationType = String(reservation.value?.reservation_type || '').trim().toLowerCase()
  const groupBillingMode = String(reservation.value?.group_billing_mode || '').trim().toLowerCase()
  const isSplitGroup = reservationType === 'group' && groupBillingMode.startsWith('split')

  actionLoading.value = true
  errorMessage.value = ''
  try {
    if (isSplitGroup) {
      const result = await callMethod(
        'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.create_pending_split_invoices',
        { reservation_name: reservation.value.name },
      )

      const createdRows = Array.isArray(result?.created) ? result.created : []
      const failedCount = Number(result?.failed_count || 0)
      if (failedCount > 0) {
        errorMessage.value = `Created ${Number(result?.created_count || 0)} invoice(s); ${failedCount} room(s) failed. Check room guests and try again.`
      }

      // Reload first so we have the latest server state.
      await loadReservation()

      // Defensive fallback: if the server did not return split_invoice on every
      // created room row (e.g. Frappe's doc.save() race), patch them in-memory
      // so the per-room Create Invoice buttons hide immediately.
      if (createdRows.length && Array.isArray(reservation.value?.rooms)) {
        const invoiceByRoomRow = new Map(
          createdRows
            .filter((entry) => entry?.room_row_name && entry?.sales_invoice)
            .map((entry) => [entry.room_row_name, entry.sales_invoice]),
        )
        reservation.value.rooms = reservation.value.rooms.map((room) => {
          if (room?.split_invoice) return room
          const splitInvoice = invoiceByRoomRow.get(room?.name)
          return splitInvoice ? { ...room, split_invoice: splitInvoice } : room
        })
      }

      return
    } else {
      await callMethod(
        'rhohotel.rhocom_hotel.doctype.hotel_reservation.hotel_reservation.create_invoice_for_reservation',
        { reservation_name: reservation.value.name },
      )
    }
    await loadReservation()
  } catch (error) {
    errorMessage.value = toUserError(error, 'Could not create invoice.')
  } finally {
    actionLoading.value = false
  }
}

loadReservation()
</script>
