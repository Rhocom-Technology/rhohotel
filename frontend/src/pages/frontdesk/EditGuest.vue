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
            <div class="mb-4">
              <p class="text-xs text-gray-500 mb-1.5">Full Name <span class="text-red-500">*</span></p>
              <input type="text" v-model="form.hotel_guest_name" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
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
                <select v-model="form.preference" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                  <option value="">—</option>
                  <option>Quiet room / High floor</option>
                  <option>Low floor</option>
                  <option>Near elevator</option>
                  <option>Non-smoking</option>
                  <option>High floor</option>
                  <option>Late Checkout</option>
                  <option>Early Check-in</option>
                </select>
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
              <p class="text-sm font-bold text-blue-700 mb-1">{{ form.hotel_guest_name || 'Guest Name' }}</p>
              <p class="text-xs text-blue-600">Type: {{ form.guest_type }}</p>
              <p class="text-xs text-blue-600">Nationality: {{ form.nationality || '—' }}</p>
              <p class="text-xs text-blue-600">Preference: {{ form.preference || '—' }}</p>
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
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { callMethodForm } from '@/lib/api'

const route = useRoute()
const router = useRouter()
const guestId = route.params.id

const loading = ref(true)
const loadError = ref(null)
const saving = ref(false)
const saveError = ref(null)
const saveSuccess = ref(false)

const originalName = ref('')

const form = reactive({
  hotel_guest_name: '',
  guest_type: 'Individual',
  title: '',
  gender: '',
  date_of_birth: '',
  phone_number: '',
  email: '',
  nationality: '',
  preference: '',
  loyalty_tier: 'Base',
  address: '',
  id_type: '',
  id_number: '',
  contact_person_name: '',
  contact_number: '',
  notes: '',
})

async function loadGuest() {
  loading.value = true
  loadError.value = null
  try {
    const g = await callMethodForm('rhohotel.rhocom_hotel.api.guest.get_guest', { name: guestId })
    originalName.value = g.name
    Object.assign(form, {
      hotel_guest_name: g.hotel_guest_name || '',
      guest_type: g.guest_type || 'Individual',
      title: g.title || '',
      gender: g.gender || '',
      date_of_birth: g.date_of_birth || '',
      phone_number: g.phone_number || '',
      email: g.email || '',
      nationality: g.nationality || '',
      preference: g.preference || '',
      loyalty_tier: g.loyalty_tier || 'Base',
      address: g.address || '',
      id_type: g.id_type || '',
      id_number: g.id_number || '',
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

  if (!form.hotel_guest_name.trim()) {
    saveError.value = 'Guest name is required.'
    return
  }

  saving.value = true
  try {
    const payload = { name: originalName.value }
    for (const [k, v] of Object.entries(form)) {
      payload[k] = String(v ?? '')
    }
    const data = await callMethodForm('rhohotel.rhocom_hotel.api.guest.update_guest', payload)
    saveSuccess.value = true
    const updated = data
    // If name changed, navigate to new route
    if (updated.name !== originalName.value) {
      router.replace({ name: 'EditGuest', params: { id: updated.name } })
    }
    originalName.value = updated.name
    setTimeout(() => { saveSuccess.value = false }, 3000)
  } catch (e) {
    saveError.value = e.message || 'Failed to save guest. Please try again.'
  } finally {
    saving.value = false
  }
}

onMounted(loadGuest)
</script>
