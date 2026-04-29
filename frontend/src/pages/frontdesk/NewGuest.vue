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
                <option>Walk-in</option>
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
              <p class="text-xs text-gray-500 mb-1.5">Phone Number</p>
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
              <p class="text-xs text-gray-500 mb-1.5">ID Type</p>
              <select v-model="form.id_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                <option value="">Select ID type</option>
                <option>Passport</option>
                <option>National ID</option>
                <option>Driver's License</option>
                <option>Voter's Card</option>
                <option>Office ID Card</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">ID Number</p>
              <input type="text" v-model="form.id_number" placeholder="Enter ID number"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
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
              <div class="w-2 h-2 rounded-full flex-shrink-0" :class="form.date_of_birth ? 'bg-green-500' : 'bg-gray-300'"></div>
              <span class="text-xs text-gray-600">Date of Birth</span>
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

const router = useRouter()
const route = useRoute()
const saving = ref(false)
const saveError = ref(null)

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

const availablePreferences = computed(() =>
  allPreferences.filter(p => !form.preferences.includes(p))
)

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

  saving.value = true
  try {
    const body = new URLSearchParams()
    // Build the phone with country code
    const fullPhone = form.phone_number ? `${form.country_code}${form.phone_number}` : ''
    
    body.append('hotel_guest_name', form.hotel_guest_name)
    body.append('first_name', form.first_name.trim())
    body.append('last_name', form.last_name.trim())
    body.append('guest_type', form.guest_type)
    if (form.title) body.append('title', form.title)
    if (form.gender) body.append('gender', form.gender)
    if (fullPhone) body.append('phone_number', fullPhone)
    if (form.email) body.append('email', form.email)
    if (form.nationality) body.append('nationality', form.nationality)
    if (form.preferences.length) body.append('preference', form.preferences.join(', '))
    if (form.date_of_birth) body.append('date_of_birth', form.date_of_birth)
    if (form.address) body.append('address', form.address)
    if (form.id_type) body.append('id_type', form.id_type)
    if (form.id_number) body.append('id_number', form.id_number)
    if (form.contact_person_name) body.append('contact_person_name', form.contact_person_name)
    if (form.contact_number) body.append('contact_number', form.contact_number)
    if (form.notes) body.append('notes', form.notes)

    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.guest.create_guest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Frappe-CSRF-Token': window.csrf_token || '',
      },
      body,
    })
    const data = await res.json()
    if (data.exc || !res.ok) {
      const msg = data._server_messages
        ? JSON.parse(data._server_messages)[0]?.message || data._server_messages
        : (data.exc || 'Failed to create guest.')
      throw new Error(msg)
    }
    const created = data.message

    // Issue #15: If we came from check-in page, route back there
    if (route.query.return_to === 'checkin') {
      router.push({ path: '/check-ins/new', query: { guest: created.name } })
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
