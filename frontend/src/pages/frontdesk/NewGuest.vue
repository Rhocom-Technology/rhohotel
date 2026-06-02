<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Guest profile • create a new guest identity, contact details, preferences, and supporting documents</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Guest Setup Control</h3>
        <p class="text-xs text-gray-400 mt-0.5">Capture guest information, contact records, nationality details, ID information, preferences, and attachment files for a new guest account.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="$router.push('/guests')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
        <button @click="createGuest" :disabled="saving"
          class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">
          {{ saving ? 'Saving…' : 'Create Guest' }}
        </button>
      </div>
    </div>

    <!-- Validation error -->
    <div v-if="saveError" class="bg-red-50 border border-red-200 rounded-xl px-5 py-3">
      <p class="text-xs font-medium text-red-600">{{ saveError }}</p>
    </div>

    <div style="display:grid;grid-template-columns:1fr 280px;gap:12px;">

      <!-- Left: Form -->
      <div class="space-y-5">

        <!-- Guest Information -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Guest Information</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Guest ID</p>
              <input type="text" placeholder="Auto generated on save"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none" readonly />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Guest Type <span class="text-red-500">*</span></p>
              <select v-model="form.guest_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select guest type</option>
                <option>Individual</option>
                <option>Corporate</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Title</p>
              <select v-model="form.title" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select title</option>
                <option>Mr</option><option>Mrs</option><option>Miss</option><option>Dr</option><option>Prof</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Gender</p>
              <select v-model="form.gender" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select gender</option>
                <option>Male</option><option>Female</option>
              </select>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">First Name <span class="text-red-500">*</span></p>
              <input type="text" v-model="form.first_name" placeholder="Enter first name"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Last Name <span class="text-red-500">*</span></p>
              <input type="text" v-model="form.last_name" placeholder="Enter last name"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Phone Number <span class="text-red-500">*</span></p>
              <div class="flex items-center gap-1">
                <select v-model="form.country_code" class="w-24 px-2 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                  <option value="+234">+234 (NG)</option>
                  <option value="+1">+1 (US)</option>
                  <option value="+44">+44 (UK)</option>
                  <option value="+91">+91 (IN)</option>
                  <option value="+27">+27 (ZA)</option>
                  <option value="+233">+233 (GH)</option>
                  <option value="+254">+254 (KE)</option>
                  <option value="+971">+971 (AE)</option>
                  <option value="+86">+86 (CN)</option>
                  <option value="+49">+49 (DE)</option>
                  <option value="+33">+33 (FR)</option>
                </select>
                <input type="text" v-model="form.phone_number" placeholder="Phone number"
                  class="flex-1 px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Email</p>
              <input type="text" v-model="form.email" placeholder="Enter email address"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Nationality</p>
              <select v-model="form.nationality" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600 focus:ring-2 focus:ring-blue-500">
                <option value="">Select nationality</option>
                <option>Nigerian</option>
                <option>Ghanaian</option>
                <option>South African</option>
                <option>Kenyan</option>
                <option>American</option>
                <option>British</option>
                <option>Canadian</option>
                <option>Indian</option>
                <option>Chinese</option>
                <option>German</option>
                <option>French</option>
                <option>Emirati</option>
                <option>Australian</option>
                <option>Brazilian</option>
                <option>Other</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Room Preference</p>
              <div class="flex flex-wrap gap-2 px-3 py-2 border border-gray-200 rounded-lg min-h-[38px]">
                <span v-for="pref in form.preferences" :key="pref"
                  class="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full flex items-center gap-1">
                  {{ pref }}
                  <button @click="removePreference(pref)" class="text-blue-400 hover:text-blue-700">&times;</button>
                </span>
                <select @change="addPreference($event)" class="flex-1 min-w-[120px] text-xs border-0 focus:outline-none bg-transparent text-gray-600">
                  <option value="">Add preference...</option>
                  <option v-for="opt in availablePreferences" :key="opt" :value="opt">{{ opt }}</option>
                </select>
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Date of Birth</p>
              <input type="date" v-model="form.date_of_birth"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Address</p>
              <input type="text" v-model="form.address" placeholder="Enter guest address"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </div>

        <!-- Identification Details -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Identification Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">ID Type <span class="text-red-500">*</span></p>
              <select v-model="form.id_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select ID type</option>
                
                <option>International Passport</option>
                <option>National ID</option>
                <option>Driver's License</option>
                <option>Voter's Card</option>
                <option>Office ID Card</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">ID Number <span class="text-red-500">*</span></p>
              <input type="text" v-model="form.id_number" placeholder="Enter ID number"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <div v-if="requiresIdDocument" style="display:grid;grid-template-columns:1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">ID Document Scan</p>
              <input
                type="file"
                accept=".pdf,image/*"
                @change="onIdDocumentChange"
                class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg bg-white file:mr-3 file:px-3 file:py-1.5 file:text-xs file:font-medium file:border-0 file:rounded-md file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              <p v-if="idDocumentName" class="mt-1 text-xs text-green-600">Selected: {{ idDocumentName }}</p>
              <p class="mt-1 text-xs text-gray-400">Accepted formats: PDF or image files (max upload size follows server settings).</p>
            </div>
          </div>
        </div>

        <!-- Contact Person -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Contact Person</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Contact Person Name</p>
              <input type="text" v-model="form.contact_person_name" placeholder="Enter contact person name"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Contact Person Number</p>
              <input type="text" v-model="form.contact_number" placeholder="Enter contact person number"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Notes</p>
            <textarea v-model="form.notes" rows="3"
              placeholder="Add service note, VIP detail, communication note, or guest handling instruction..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
          </div>
        </div>
      </div>

      <!-- Right: Setup Summary -->
      <div class="space-y-4">
        <h3 class="text-sm font-bold text-gray-900">Setup Summary</h3>

        <div>
          <p class="text-xs text-gray-500 mb-2">Guest Preview</p>
          <div class="bg-blue-50 rounded-xl border border-blue-200 px-4 py-4">
            <p class="text-sm font-bold text-blue-700 mb-1">{{ form.first_name || form.last_name ? `${form.first_name} ${form.last_name}`.trim() : 'New Guest Preview' }}</p>
            <p class="text-xs text-blue-600">Type: {{ form.guest_type || 'Not selected' }}</p>
            <p class="text-xs text-blue-600">Phone: {{ form.phone_number ? `${form.country_code}${form.phone_number}` : 'Not provided' }}</p>
            <p class="text-xs text-blue-600">Nationality: {{ form.nationality || 'Not provided' }}</p>
            <p class="text-xs text-blue-600">Preference: {{ form.preferences.length ? form.preferences.join(', ') : 'Not selected' }}</p>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Loyalty Default</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
            <p class="text-xs font-bold text-gray-900 mb-1">Standard Guest Level</p>
            <p class="text-xs text-gray-500">Reward level starts at base tier</p>
            <p class="text-xs text-gray-500">Stay count begins from first check-in</p>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Required Fields</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-1.5">
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full flex-shrink-0" :class="form.first_name ? 'bg-green-500' : 'bg-gray-300'"></div>
              <span class="text-xs text-gray-600">First Name</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full flex-shrink-0" :class="form.last_name ? 'bg-green-500' : 'bg-gray-300'"></div>
              <span class="text-xs text-gray-600">Last Name</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full flex-shrink-0" :class="form.guest_type ? 'bg-green-500' : 'bg-gray-300'"></div>
              <span class="text-xs text-gray-600">Guest Type</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full flex-shrink-0" :class="form.phone_number ? 'bg-green-500' : 'bg-gray-300'"></div>
              <span class="text-xs text-gray-600">Phone Number</span>
            </div>

            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full flex-shrink-0" :class="form.id_type ? 'bg-green-500' : 'bg-gray-300'"></div>
              <span class="text-xs text-gray-600">ID Type</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full flex-shrink-0" :class="form.id_number ? 'bg-green-500' : 'bg-gray-300'"></div>
              <span class="text-xs text-gray-600">ID Number</span>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { callMethodForm, requestApi } from '@/lib/api'
import { buildPhoneWithCountry, isValidPhone, phoneError } from '@/lib/phone'

const router = useRouter()
const route = useRoute()
const saving = ref(false)
const saveError = ref(null)
const idDocumentFile = ref(null)

const allPreferences = [
  'Quiet room / High floor',
  'Low floor',
  'Near elevator',
  'Non-smoking',
  'High floor',
  'Late Checkout',
  'Early Check-in',
  'Extra Towels',
  'Extra Pillows',
  'Ground Floor',
]

const form = reactive({
  first_name: '',
  last_name: '',
  hotel_guest_name: '',
  guest_type: '',
  title: '',
  gender: '',
  country_code: '+234',
  phone_number: '',
  email: '',
  nationality: '',
  preferences: [],
  date_of_birth: '',
  address: '',
  id_type: '',
  id_number: '',
  contact_person_name: '',
  contact_number: '',
  notes: '',
})

if (route.query.type === 'Corporate' || route.query.guest_type === 'Corporate') {
  form.guest_type = 'Corporate'
} else if (route.query.type === 'Individual' || route.query.guest_type === 'Individual') {
  form.guest_type = 'Individual'
}

const availablePreferences = computed(() =>
  allPreferences.filter(p => !form.preferences.includes(p))
)

const requiresIdDocument = computed(() => Boolean(form.id_type))

const idDocumentName = computed(() => idDocumentFile.value?.name || '')

function addPreference(event) {
  const val = event.target.value
  if (val && !form.preferences.includes(val)) {
    form.preferences.push(val)
  }
  event.target.value = ''
}

function removePreference(pref) {
  form.preferences = form.preferences.filter(p => p !== pref)
}

function onIdDocumentChange(event) {
  const [file] = event.target.files || []
  idDocumentFile.value = file || null
}

async function uploadIdDocument(guestName) {
  if (!idDocumentFile.value) return

  const body = new FormData()
  body.append('file', idDocumentFile.value)
  body.append('doctype', 'Hotel Guest')
  body.append('docname', guestName)
  body.append('fieldname', 'id_document_scan')
  body.append('is_private', '1')

  await requestApi('/api/method/upload_file', {
    method: 'POST',
    body,
  })
}

async function createGuest() {
  saveError.value = null

  // Combine first + last name
  form.hotel_guest_name = `${form.first_name.trim()} ${form.last_name.trim()}`.trim()

  if (!form.hotel_guest_name) {
    saveError.value = 'First name and last name are required.'
    return
  }
  if (!form.guest_type) {
    saveError.value = 'Guest type is required.'
    return
  }
  if (!form.phone_number) {
    saveError.value = 'Phone number is required.'
    return
  }
  const fullPhone = buildPhoneWithCountry(form.country_code, form.phone_number)
  if (!isValidPhone(fullPhone, { required: true })) {
    saveError.value = phoneError('Phone number')
    return
  }
  if (form.contact_number && !isValidPhone(form.contact_number)) {
    saveError.value = phoneError('Contact person number')
    return
  }
  if (!form.id_type) {
    saveError.value = 'ID type is required.'
    return
  }
  if (!form.id_number) {
    saveError.value = 'ID number is required.'
    return
  }

  saving.value = true
  try {
    const created = await callMethodForm('rhohotel.rhocom_hotel.api.guest.create_guest', {
      hotel_guest_name: form.hotel_guest_name,
      guest_type: form.guest_type,
      title: form.title,
      gender: form.gender,
      phone_number: fullPhone,
      email: form.email,
      nationality: form.nationality,
      preference: form.preferences.length ? form.preferences.join(', ') : '',
      date_of_birth: form.date_of_birth,
      address: form.address,
      id_type: form.id_type,
      id_number: form.id_number,
      contact_person_name: form.contact_person_name,
      contact_number: form.contact_number,
      notes: form.notes,
    })

    await uploadIdDocument(created.name)

    // Route back to the correct context
    if (route.query.return_to === 'checkin') {
      router.push({
        path: '/check-ins/new',
        query: {
          guest: created.name,
          guest_name: created.hotel_guest_name || form.hotel_guest_name,
          guest_phone: fullPhone,
          guest_email: form.email || '',
          reservation: route.query.reservation || '',
          canonical_reservation: route.query.canonical_reservation || route.query.reservation || '',
          room: route.query.room || '',
          room_type: route.query.room_type || '',
          nights: route.query.nights || '',
          check_in_dt: route.query.check_in_dt || '',
        },
      })
    } else if (route.query.return_to === 'new_reservation') {
      router.push({
        name: 'NewReservation',
        query: {
          type: route.query.type || form.guest_type || 'Individual',
          guest: created.name,
          guest_name: created.hotel_guest_name || form.hotel_guest_name,
          guest_phone: fullPhone,
          guest_email: form.email || '',
        },
      })
    } else if (route.query.return_to === 'saved_reservation' && route.query.reservation_id) {
      router.push({
        name: 'SavedReservation',
        params: { id: route.query.reservation_id },
      })
    } else {
      router.push({ name: 'GuestProfile', params: { id: created.name } })
    }
  } catch (e) {
    saveError.value = e.message || 'Failed to create guest. Please try again.'
  } finally {
    saving.value = false
  }
}
</script>
