<template>
  <div class="space-y-5">

    <!-- Loading -->
    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 px-6 py-16 text-center">
      <p class="text-xs text-gray-400">Loading guest record…</p>
    </div>

    <!-- Error loading -->
    <div v-else-if="loadError" class="bg-white rounded-xl border border-gray-200 px-6 py-16 text-center">
      <p class="text-xs text-red-500 mb-3">{{ loadError }}</p>
      <button @click="$router.push('/guests')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Back to Guest List</button>
    </div>

    <template v-else>
      <!-- Breadcrumb -->
      <div class="text-xs text-gray-400">
        Guest Profile / <span class="text-gray-600">Edit Existing Guest</span>
      </div>

      <!-- Control Bar -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Edit Guest Record</h3>
          <p class="text-xs text-gray-400 mt-0.5">Update guest information, contact records, preferences, nationality details, ID information, and supporting attachment files.</p>
        </div>
        <div class="flex items-center gap-2">
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            @click="$router.push({ name: 'GuestProfile', params: { id: guestId } })">View Profile</button>
          <button @click="resetForm" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Reset Changes</button>
          <button @click="saveGuest" :disabled="saving"
            class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">
            {{ saving ? 'Saving…' : 'Save Changes' }}
          </button>
        </div>
      </div>

      <!-- Save error -->
      <div v-if="saveError" class="bg-red-50 border border-red-200 rounded-xl px-5 py-3">
        <p class="text-xs font-medium text-red-600">{{ saveError }}</p>
      </div>

      <!-- Save success -->
      <div v-if="saveSuccess" class="bg-green-50 border border-green-200 rounded-xl px-5 py-3">
        <p class="text-xs font-medium text-green-600">Guest record updated successfully.</p>
      </div>

      <div style="display:grid;grid-template-columns:1fr 280px;gap:12px;">

        <!-- Left: Form -->
        <div class="space-y-5">

          <!-- Guest Information -->
          <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Guest Information</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Guest Type</p>
                <select v-model="form.guest_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                  <option>Individual</option><option>Corporate</option><option>Walk-in</option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Title</p>
                <select v-model="form.title" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                  <option value="">—</option>
                  <option>Mr</option><option>Mrs</option><option>Miss</option><option>Dr</option><option>Prof</option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Gender</p>
                <select v-model="form.gender" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                  <option value="">—</option><option>Male</option><option>Female</option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Date of Birth</p>
                <input type="date" v-model="form.date_of_birth" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <div class="mb-4" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">First Name <span class="text-red-500">*</span></p>
                <input type="text" v-model="form.first_name" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Last Name <span class="text-red-500">*</span></p>
                <input type="text" v-model="form.last_name" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Phone Number</p>
                <input type="text" v-model="form.phone_number" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Email</p>
                <input type="text" v-model="form.email" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Nationality</p>
                <input type="text" v-model="form.nationality" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
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
                <p class="text-xs text-gray-500 mb-1.5">Loyalty Tier</p>
                <select v-model="form.loyalty_tier" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                  <option>Base</option><option>Silver</option><option>Gold</option>
                  <option>Platinum</option><option>VIP</option><option>Corporate</option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Address</p>
                <input type="text" v-model="form.address" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
          </div>

          <!-- Identification Details -->
          <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Identification Details</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">ID Type</p>
                <select v-model="form.id_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                  <option value="">Select ID type</option>
                  <option>Passport</option>
                  <option>International</option>
                  <option>National ID</option>
                  <option>Driver's License</option>
                  <option>Voter's Card</option>
                  <option>Office ID Card</option>
                </select>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">ID Number</p>
                <input type="text" v-model="form.id_number" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>

            <div v-if="form.id_type" style="display:grid;grid-template-columns:1fr;gap:12px;">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">ID Document Scan</p>
                <input
                  type="file"
                  accept=".pdf,image/*"
                  @change="onIdDocumentChange"
                  class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg bg-white file:mr-3 file:px-3 file:py-1.5 file:text-xs file:font-medium file:border-0 file:rounded-md file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                <p v-if="idDocumentName" class="mt-1 text-xs text-green-600">Selected: {{ idDocumentName }}</p>
                <a
                  v-if="form.id_document_scan"
                  :href="form.id_document_scan"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="mt-1 inline-block text-xs text-blue-600 hover:underline"
                >View current uploaded document</a>
              </div>
            </div>
          </div>

          <!-- Contact Person -->
          <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Contact Person</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Contact Person Name</p>
                <input type="text" v-model="form.contact_person_name" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Contact Person Number</p>
                <input type="text" v-model="form.contact_number" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Notes</p>
              <textarea v-model="form.notes" rows="3"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
            </div>
          </div>
        </div>

        <!-- Right: Edit Summary -->
        <div class="space-y-4">
          <h3 class="text-sm font-bold text-gray-900">Edit Summary</h3>

          <div>
            <p class="text-xs text-gray-500 mb-2">Guest Preview</p>
            <div class="bg-blue-50 rounded-xl border border-blue-200 px-4 py-4">
              <p class="text-sm font-bold text-blue-700 mb-1">{{ form.first_name || form.last_name ? `${form.first_name} ${form.last_name}`.trim() : form.hotel_guest_name || 'Guest Name' }}</p>
              <p class="text-xs text-blue-600">Type: {{ form.guest_type }}</p>
              <p class="text-xs text-blue-600">Nationality: {{ form.nationality || '—' }}</p>
              <p class="text-xs text-blue-600">Preference: {{ form.preferences.length ? form.preferences.join(', ') : '—' }}</p>
              <p class="text-xs text-blue-600">Loyalty: {{ form.loyalty_tier || 'Base' }}</p>
            </div>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-2">Record Status</p>
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2">
              <div class="flex items-center gap-2">
                <div class="w-2.5 h-2.5 rounded-full bg-green-500"></div>
                <span class="text-xs text-gray-700">Active guest profile</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-2.5 h-2.5 rounded-full bg-green-500"></div>
                <span class="text-xs text-gray-700">Eligible for reservations and check-in</span>
              </div>
            </div>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-2">Quick Actions</p>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
              <button @click="$router.push({ name: 'GuestProfile', params: { id: guestId } })"
                class="px-3 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">View Profile</button>
              <button @click="$router.push('/guests')"
                class="px-3 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Guest List</button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { callMethodForm, requestApi } from '@/lib/api'
import { isValidPhone, phoneError } from '@/lib/phone'

const route = useRoute()
const router = useRouter()
const guestId = computed(() => String(route.params.id || ''))

const loading = ref(true)
const loadError = ref(null)
const saving = ref(false)
const saveError = ref(null)
const saveSuccess = ref(false)
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

const originalName = ref('')

const form = reactive({
  first_name: '',
  last_name: '',
  hotel_guest_name: '',
  guest_type: 'Individual',
  title: '',
  gender: '',
  date_of_birth: '',
  phone_number: '',
  email: '',
  nationality: '',
  preferences: [],
  loyalty_tier: 'Base',
  address: '',
  id_type: '',
  id_number: '',
  id_document_scan: '',
  contact_person_name: '',
  contact_number: '',
  notes: '',
})

const availablePreferences = computed(() =>
  allPreferences.filter(p => !form.preferences.includes(p))
)

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

  const payload = await requestApi('/api/method/upload_file', {
    method: 'POST',
    body,
  })

  form.id_document_scan = payload?.message?.file_url || form.id_document_scan
}

async function loadGuest(name = guestId.value) {
  if (!name) return
  loading.value = true
  loadError.value = null
  try {
    const g = await callMethodForm('rhohotel.rhocom_hotel.api.guest.get_guest', { name })
    originalName.value = g.name
    const nameParts = (g.hotel_guest_name || '').trim().split(/\s+/)
    const firstName = nameParts.slice(0, -1).join(' ') || nameParts[0] || ''
    const lastName = nameParts.length > 1 ? nameParts[nameParts.length - 1] : ''
    Object.assign(form, {
      first_name: firstName,
      last_name: lastName,
      hotel_guest_name: g.hotel_guest_name || '',
      guest_type: g.guest_type || 'Individual',
      title: g.title || '',
      gender: g.gender || '',
      date_of_birth: g.date_of_birth || '',
      phone_number: g.phone_number || '',
      email: g.email || '',
      nationality: g.nationality || '',
      preferences: (g.preference || '').split(',').map(v => v.trim()).filter(Boolean),
      loyalty_tier: g.loyalty_tier || 'Base',
      address: g.address || '',
      id_type: g.id_type || '',
      id_number: g.id_number || '',
      id_document_scan: g.id_document_scan || '',
      contact_person_name: g.contact_person_name || '',
      contact_number: g.contact_number || '',
      notes: g.notes || '',
    })
  } catch (e) {
    loadError.value = e.message || 'Failed to load guest.'
  } finally {
    loading.value = false
  }
}

function resetForm() {
  loadGuest()
  saveError.value = null
  saveSuccess.value = false
}

async function saveGuest() {
  saveError.value = null
  saveSuccess.value = false

  if (!form.first_name.trim() && !form.last_name.trim() && !form.hotel_guest_name.trim()) {
    saveError.value = 'Guest name is required.'
    return
  }
  const fullName = form.first_name || form.last_name
    ? `${form.first_name.trim()} ${form.last_name.trim()}`.trim()
    : form.hotel_guest_name.trim()
  if (!fullName) {
    saveError.value = 'Guest name is required.'
    return
  }
  if (!isValidPhone(form.phone_number, { required: true })) {
    saveError.value = phoneError('Phone number')
    return
  }
  if (form.contact_number && !isValidPhone(form.contact_number)) {
    saveError.value = phoneError('Contact person number')
    return
  }
  saving.value = true
  try {
    const body = new URLSearchParams()
    body.append('name', originalName.value)
    body.append('hotel_guest_name', fullName)
    body.append('guest_type', form.guest_type)
    body.append('title', form.title || '')
    body.append('gender', form.gender || '')
    body.append('date_of_birth', form.date_of_birth || '')
    body.append('phone_number', form.phone_number || '')
    body.append('email', form.email || '')
    body.append('nationality', form.nationality || '')
    body.append('preference', form.preferences.length ? form.preferences.join(', ') : '')
    body.append('loyalty_tier', form.loyalty_tier || 'Base')
    body.append('address', form.address || '')
    body.append('id_type', form.id_type || '')
    body.append('id_number', form.id_number || '')
    body.append('id_document_scan', form.id_document_scan || '')
    body.append('contact_person_name', form.contact_person_name || '')
    body.append('contact_number', form.contact_number || '')
    body.append('notes', form.notes || '')

    const payload = await requestApi('/api/method/rhohotel.rhocom_hotel.api.guest.update_guest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body,
    })

    const data = payload?.message
    const updatedName = data?.name || originalName.value
    await uploadIdDocument(updatedName)

    saveSuccess.value = true
    // If the document was renamed, keep route actions and future saves on the new id.
    if (updatedName !== guestId.value) {
      await router.replace({ name: 'EditGuest', params: { id: updatedName } })
    }
    await loadGuest(updatedName)
    setTimeout(() => { saveSuccess.value = false }, 3000)
  } catch (e) {
    saveError.value = e.message || 'Failed to save guest. Please try again.'
  } finally {
    saving.value = false
  }
}

onMounted(loadGuest)

watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    loadGuest(String(newId))
  }
})
</script>
