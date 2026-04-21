<template>
  <div class="p-6 space-y-4">
    <div class="flex items-start justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">{{ reservationType === 'Corporate' ? 'Corporate Reservation' : 'New Reservation' }}</h1>
        <p class="text-xs text-gray-400 mt-1">Create reservation records directly in Hotel Front Desk Reservation.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="emit('close')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
        <button :disabled="isSaving" @click="saveReservation(false)" class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 disabled:opacity-40">Save Draft</button>
        <button :disabled="isSaving" @click="saveReservation(true)" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40">Submit</button>
      </div>
    </div>

    <div v-if="errorMessage" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-600">{{ errorMessage }}</div>
    <div v-if="successMessage" class="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-xs text-green-700">{{ successMessage }}</div>

    <div class="bg-white rounded-xl border border-gray-200 p-5">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Reservation Type</p>
          <select v-model="reservationType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option>Individual</option>
            <option>Corporate</option>
          </select>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Arrival Date</p>
          <input v-model="form.from_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Departure Date</p>
          <input v-model="form.to_date" type="date" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Nights</p>
          <div class="px-3 py-2.5 text-xs bg-gray-50 border border-gray-200 rounded-lg text-gray-700">{{ nightsCount }}</div>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-5">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Guest / Booker</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
        <div v-if="reservationType === 'Corporate'">
          <p class="text-xs text-gray-500 mb-1.5">Corporate Guest</p>
          <select v-model="form.corporate_guest" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">Select corporate guest</option>
            <option v-for="g in corporateGuests" :key="g.name" :value="g.name">{{ g.hotel_guest_name || g.name }}</option>
          </select>
        </div>
        <div v-else>
          <p class="text-xs text-gray-500 mb-1.5">Individual Guest</p>
          <select v-model="form.individual_guest" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">Select guest</option>
            <option v-for="g in individualGuests" :key="g.name" :value="g.name">{{ g.hotel_guest_name || g.name }}</option>
          </select>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Guest/Contact Name</p>
          <input v-model="form.primary_guest_name" type="text" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Contact Phone</p>
          <input v-model="form.primary_guest_phone" type="text" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Contact Email</p>
          <input v-model="form.primary_guest_email" type="email" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-5">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Rooms & Pricing</h3>
      <div class="grid grid-cols-1 md:grid-cols-5 gap-3">
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
          <select v-model="selectedRoomType" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">All Types</option>
            <option v-for="t in roomTypes" :key="t.name" :value="t.name">{{ t.room_type || t.name }}</option>
          </select>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Available Room</p>
          <select v-model="selectedRoom" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">Select room</option>
            <option v-for="room in availableRooms" :key="room.name" :value="room.name">{{ room.name }} • {{ room.room_type }}</option>
          </select>
        </div>
        <div class="flex items-end">
          <button @click="addRoom" class="w-full px-3 py-2.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Add Room</button>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Discount Type</p>
          <select v-model="form.discount_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none">
            <option value="">None</option>
            <option>Percentage</option>
            <option>Fixed Amount</option>
          </select>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Discount</p>
          <input v-model.number="form.discount" type="number" min="0" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none" />
        </div>
      </div>

      <div class="mt-4 overflow-x-auto border border-gray-100 rounded-lg">
        <table class="w-full">
          <thead class="bg-gray-50">
            <tr>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Room</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Type</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Rate/Night</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Nights</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Total</th>
              <th class="text-left text-xs font-medium text-gray-500 px-3 py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="selectedRooms.length === 0">
              <td colspan="6" class="px-3 py-4 text-center text-xs text-gray-300">No rooms selected</td>
            </tr>
            <tr v-for="room in selectedRooms" :key="room.name" class="border-t border-gray-100">
              <td class="px-3 py-2 text-xs text-gray-700">{{ room.name }}</td>
              <td class="px-3 py-2 text-xs text-gray-700">{{ room.room_type }}</td>
              <td class="px-3 py-2 text-xs text-gray-700">{{ formatCurrency(room.rate_per_night) }}</td>
              <td class="px-3 py-2 text-xs text-gray-700">{{ nightsCount }}</td>
              <td class="px-3 py-2 text-xs text-gray-700">{{ formatCurrency(room.rate_per_night * nightsCount) }}</td>
              <td class="px-3 py-2 text-xs">
                <button @click="removeRoom(room.name)" class="text-red-500 hover:text-red-600">Remove</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-5">
      <h3 class="text-sm font-bold text-gray-900 mb-3">Summary</h3>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div class="px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-100 text-xs">Subtotal: <span class="font-semibold">{{ formatCurrency(subTotal) }}</span></div>
        <div class="px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-100 text-xs">Discount: <span class="font-semibold">{{ formatCurrency(discountAmount) }}</span></div>
        <div class="px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-100 text-xs">Total Rooms: <span class="font-semibold">{{ selectedRooms.length }}</span></div>
        <div class="px-3 py-2.5 rounded-lg bg-blue-50 border border-blue-100 text-xs">Grand Total: <span class="font-semibold text-blue-700">{{ formatCurrency(grandTotal) }}</span></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { createResource } from 'frappe-ui'

const props = defineProps({ type: { type: String, required: true } })
const emit = defineEmits(['close', 'saved'])

const reservationType = ref(props.type === 'Corporate' ? 'Corporate' : 'Individual')
const form = ref({
  from_date: '',
  to_date: '',
  primary_guest_name: '',
  primary_guest_email: '',
  primary_guest_phone: '',
  corporate_guest: '',
  individual_guest: '',
  discount_type: '',
  discount: 0,
})

const errorMessage = ref('')
const successMessage = ref('')
const isSaving = ref(false)

const selectedRoomType = ref('')
const selectedRoom = ref('')
const selectedRooms = ref([])
const availableRooms = ref([])

const corporateGuestsResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Hotel Guest',
    fields: ['name', 'hotel_guest_name', 'email', 'phone_number', 'customer'],
    filters: [['guest_type', '=', 'Corporate']],
    order_by: 'hotel_guest_name asc',
    limit_page_length: 500,
  },
  auto: true,
})

const individualGuestsResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Hotel Guest',
    fields: ['name', 'hotel_guest_name', 'email', 'phone_number', 'customer'],
    filters: [['guest_type', '=', 'Individual']],
    order_by: 'hotel_guest_name asc',
    limit_page_length: 500,
  },
  auto: true,
})

const roomTypesResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Hotel Room Type',
    fields: ['name', 'room_type'],
    filters: [['is_active', '=', 1]],
    order_by: 'room_type asc',
    limit_page_length: 500,
  },
  auto: true,
})

const corporateGuests = computed(() => corporateGuestsResource.data || [])
const individualGuests = computed(() => individualGuestsResource.data || [])
const roomTypes = computed(() => roomTypesResource.data || [])

const nightsCount = computed(() => {
  if (!form.value.from_date || !form.value.to_date) return 0
  const diff = Math.round((new Date(form.value.to_date) - new Date(form.value.from_date)) / 86400000)
  return diff > 0 ? diff : 0
})

const subTotal = computed(() => selectedRooms.value.reduce((acc, room) => acc + Number(room.rate_per_night || 0) * nightsCount.value, 0))
const discountAmount = computed(() => {
  const discount = Number(form.value.discount || 0)
  if (!discount || !form.value.discount_type) return 0
  if (form.value.discount_type === 'Percentage') return (subTotal.value * discount) / 100
  return discount
})
const grandTotal = computed(() => Math.max(0, subTotal.value - discountAmount.value))

watch(
  () => [form.value.from_date, form.value.to_date, selectedRoomType.value],
  () => {
    availableRooms.value = []
    selectedRoom.value = ''
    if (form.value.from_date && form.value.to_date && nightsCount.value > 0) {
      loadAvailableRooms()
    }
  },
)

watch(
  () => form.value.corporate_guest,
  (guestName) => {
    if (!guestName) return
    const guest = corporateGuests.value.find((g) => g.name === guestName)
    if (!guest) return
    form.value.primary_guest_name = form.value.primary_guest_name || guest.hotel_guest_name || ''
    form.value.primary_guest_email = form.value.primary_guest_email || guest.email || ''
    form.value.primary_guest_phone = form.value.primary_guest_phone || guest.phone_number || ''
  },
)

watch(
  () => form.value.individual_guest,
  (guestName) => {
    if (!guestName) return
    const guest = individualGuests.value.find((g) => g.name === guestName)
    if (!guest) return
    form.value.primary_guest_name = form.value.primary_guest_name || guest.hotel_guest_name || ''
    form.value.primary_guest_email = form.value.primary_guest_email || guest.email || ''
    form.value.primary_guest_phone = form.value.primary_guest_phone || guest.phone_number || ''
  },
)

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

async function loadAvailableRooms() {
  try {
    const rows = await callApi('rhohotel.rhocom_hotel.doctype.hotel_front_desk_reservation.hotel_front_desk_reservation.get_available_rooms', {
      from_date: form.value.from_date,
      to_date: form.value.to_date,
      room_type: selectedRoomType.value || undefined,
    })
    availableRooms.value = Array.isArray(rows) ? rows : []
  } catch {
    availableRooms.value = []
  }
}

function addRoom() {
  if (!selectedRoom.value) return
  const room = availableRooms.value.find((r) => r.name === selectedRoom.value)
  if (!room) return
  if (selectedRooms.value.some((r) => r.name === room.name)) return
  selectedRooms.value.push({ ...room })
}

function removeRoom(roomName) {
  selectedRooms.value = selectedRooms.value.filter((r) => r.name !== roomName)
}

function validateForm() {
  if (!form.value.from_date || !form.value.to_date || nightsCount.value < 1) return 'Select valid stay dates.'
  if (!form.value.primary_guest_name || !form.value.primary_guest_phone) return 'Guest name and phone are required.'
  if (selectedRooms.value.length === 0) return 'Add at least one room.'
  if (reservationType.value === 'Corporate' && !form.value.corporate_guest) return 'Corporate reservation requires a corporate guest.'
  return ''
}

async function saveReservation(submitAfterSave) {
  errorMessage.value = ''
  successMessage.value = ''

  const validationError = validateForm()
  if (validationError) {
    errorMessage.value = validationError
    return
  }

  isSaving.value = true
  try {
    const guestDoc = reservationType.value === 'Corporate'
      ? corporateGuests.value.find((g) => g.name === form.value.corporate_guest)
      : individualGuests.value.find((g) => g.name === form.value.individual_guest)

    const doc = {
      doctype: 'Hotel Front Desk Reservation',
      reservation_type: reservationType.value,
      from_date: form.value.from_date,
      to_date: form.value.to_date,
      primary_guest_name: form.value.primary_guest_name,
      primary_guest_email: form.value.primary_guest_email,
      primary_guest_phone: form.value.primary_guest_phone,
      corporate_guest: reservationType.value === 'Corporate' ? form.value.corporate_guest : undefined,
      customer: guestDoc?.customer || undefined,
      discount_type: form.value.discount_type || undefined,
      discount: Number(form.value.discount || 0),
      rooms: selectedRooms.value.map((room) => ({
        room_number: room.name,
        guest_name: form.value.primary_guest_name,
        guest_email: form.value.primary_guest_email,
        guest_phone: form.value.primary_guest_phone,
      })),
    }

    const inserted = await callApi('frappe.client.insert', { doc })
    let target = inserted

    if (submitAfterSave) {
      target = await callApi('frappe.client.submit', { doc: inserted })
      successMessage.value = 'Reservation submitted successfully.'
    } else {
      successMessage.value = 'Reservation saved as draft.'
    }

    emit('saved', target)
  } catch (error) {
    errorMessage.value = String(error?.message || 'Could not save reservation.')
  } finally {
    isSaving.value = false
  }
}

function formatCurrency(amount) {
  return `₦${Number(amount || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`
}
</script>