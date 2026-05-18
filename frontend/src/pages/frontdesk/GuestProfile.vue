<template>
  <div class="space-y-5">

    <!-- Loading -->
    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 px-6 py-16 text-center">
      <p class="text-xs text-gray-400">Loading guest profile…</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-white rounded-xl border border-gray-200 px-6 py-16 text-center">
      <p class="text-xs text-red-500 mb-3">{{ error }}</p>
      <button @click="$router.push('/guests')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Back to Guest List</button>
    </div>

    <template v-else-if="guest">

      <!-- Guest Header -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <div class="flex items-start justify-between">
          <div class="flex items-start gap-4">
            <div class="w-14 h-14 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
              :style="avatarStyle(guest.hotel_guest_name)">
              {{ initials(guest.hotel_guest_name) }}
            </div>
            <div>
              <h1 class="text-2xl font-bold text-gray-900 mb-1">{{ guest.hotel_guest_name }}</h1>
              <p class="text-xs text-gray-500 mb-1">
                {{ guest.phone_number || '—' }} • {{ guest.email || '—' }} • {{ guest.nationality || '—' }}
              </p>
              <p class="text-xs text-gray-400">
                Guest Type: {{ guest.guest_type }}
                <span v-if="guest.active_checkin"> • Last Stay: {{ formatDate(guest.active_checkin.check_in_datetime) }}</span>
              </p>
              <div class="flex items-center gap-2 mt-2 flex-wrap">
                <span class="px-2.5 py-0.5 text-xs font-medium rounded-full" :class="loyaltyClass(guest.loyalty_tier)">
                  {{ guest.loyalty_tier || 'Base' }}
                </span>
                <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">
                  {{ guest.guest_type }}
                </span>
                <span v-if="guest.current_status === 'In-House'"
                  class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">
                  Checked In
                </span>
              </div>
            </div>
          </div>
          <!-- Current Stay Snapshot -->
          <div v-if="guest.active_checkin" class="bg-gray-50 rounded-xl border border-gray-200 px-5 py-4 text-xs" style="min-width:220px;">
            <p class="font-bold text-gray-900 mb-2">Current Stay Snapshot</p>
            <p class="text-gray-600 mb-0.5">Room: {{ guest.active_checkin.room_number }}</p>
            <p class="text-gray-600 mb-0.5">Check-in: {{ formatDate(guest.active_checkin.check_in_datetime) }}</p>
            <p class="text-gray-600 mb-0.5">Check-out: {{ formatDate(guest.active_checkin.expected_check_out_datetime) }}</p>
            <p v-if="guest.active_checkin.total_outstanding_amount > 0" class="font-bold text-red-500 mt-1">
              Balance: {{ formatCurrency(guest.active_checkin.total_outstanding_amount) }}
            </p>
          </div>
          <div v-else class="flex items-center">
            <button @click="$router.push('/guests')"
              class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              ← Guest List
            </button>
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Total Stays</p>
          <p class="text-3xl font-bold text-gray-900">{{ guest.total_stays }}</p>
          <p class="text-xs font-medium text-green-600 mt-1">{{ guest.total_stays > 5 ? 'Frequent returning guest' : 'Registered guest' }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Lifetime Spend</p>
          <p class="text-3xl font-bold text-gray-900">{{ formatCurrency(guest.lifetime_spend) }}</p>
          <p class="text-xs font-medium text-blue-600 mt-1">Completed stays</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Loyalty Tier</p>
          <p class="text-3xl font-bold text-gray-900">{{ guest.loyalty_tier || 'Base' }}</p>
          <p class="text-xs font-medium text-yellow-600 mt-1">Loyalty level</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <p class="text-xs text-gray-400 mb-2">Current Status</p>
          <p class="text-3xl font-bold text-gray-900">{{ guest.current_status }}</p>
          <p class="text-xs font-medium mt-1" :class="guest.current_status === 'In-House' ? 'text-green-600' : 'text-gray-400'">
            {{ guest.current_status === 'In-House' ? 'Currently in hotel' : 'Not checked in' }}
          </p>
        </div>
      </div>

      <!-- Tabs -->
      <div class="bg-white rounded-xl border border-gray-200 px-6">
        <div class="flex items-center gap-1 border-b border-gray-100 overflow-x-auto">
          <button v-for="tab in tabs" :key="tab"
            @click="activeTab = tab"
            class="px-4 py-3.5 text-xs font-medium whitespace-nowrap transition-colors border-b-2 -mb-px"
            :class="activeTab === tab ? 'text-white border-gray-900 bg-gray-900 rounded-lg mb-1' : 'text-gray-500 border-transparent hover:text-gray-700'">
            {{ tab }}
          </button>
        </div>
      </div>

      <!-- Profile Tab -->
      <div v-if="activeTab === 'Profile'" style="display:grid;grid-template-columns:1fr 300px;gap:12px;">

        <!-- Left -->
        <div class="space-y-5">
          <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-bold text-gray-900">Guest Information</h3>
              <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                @click="$router.push({ name: 'EditGuest', params: { id: guestId } })">Edit Guest</button>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Full Name</p>
                <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ guest.hotel_guest_name }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Guest Type</p>
                <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ guest.guest_type }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Phone</p>
                <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ guest.phone_number || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Email</p>
                <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ guest.email || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Nationality</p>
                <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ guest.nationality || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Gender</p>
                <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ guest.gender || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Date of Birth</p>
                <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ guest.date_of_birth || '—' }}</div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1.5">Address</p>
                <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ guest.address || '—' }}</div>
              </div>
              <div style="grid-column:span 2;">
                <p class="text-xs text-gray-500 mb-1.5">ID Type / Number</p>
                <div class="px-3 py-2.5 text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">
                  {{ guest.id_type || '—' }} {{ guest.id_number ? '• ' + guest.id_number : '' }}
                </div>
              </div>
              <div style="grid-column:span 2;" v-if="guest.id_document_scan">
                <p class="text-xs text-gray-500 mb-1.5">Uploaded ID Document</p>
                <!-- Image preview -->
                <div v-if="isIdImage" class="relative">
                  <img
                    :src="guest.id_document_scan"
                    alt="ID Document"
                    class="w-full max-h-64 object-contain rounded-xl border border-gray-200 bg-gray-50 cursor-pointer"
                    @click="showDocPreview = true"
                  />
                  <button
                    @click="showDocPreview = true"
                    class="absolute bottom-2 right-2 px-3 py-1.5 text-xs font-medium text-white bg-gray-900 bg-opacity-70 rounded-lg hover:bg-opacity-90">
                    View Full Size
                  </button>
                </div>
                <!-- PDF / other -->
                <div v-else class="px-4 py-4 bg-gray-50 border border-gray-200 rounded-xl flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-lg bg-red-50 border border-red-100 flex items-center justify-center text-red-500 font-bold text-xs">PDF</div>
                    <div>
                      <p class="text-xs font-semibold text-gray-800">{{ idDocFileName }}</p>
                      <p class="text-xs text-gray-400">Click to preview</p>
                    </div>
                  </div>
                  <button
                    @click="showDocPreview = true"
                    class="px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
                    Preview
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="guest.preference" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <h3 class="text-sm font-bold text-gray-900 mb-3">Guest Preferences</h3>
            <div class="flex items-center gap-2 flex-wrap px-3 py-3 bg-gray-50 border border-gray-200 rounded-lg">
              <span
                v-for="pref in preferenceList"
                :key="pref"
                class="px-3 py-1 text-xs font-medium bg-blue-100 text-blue-600 rounded-full"
              >{{ pref }}</span>
            </div>
          </div>

          <div v-if="guest.notes" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <h3 class="text-sm font-bold text-gray-900 mb-3">Notes</h3>
            <p class="text-xs text-gray-700">{{ guest.notes }}</p>
          </div>

          <div v-if="guest.timeline && guest.timeline.length" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">Stay Timeline</h3>
            <div class="space-y-4">
              <div v-for="t in guest.timeline" :key="t.date" class="flex items-start gap-3">
                <div class="w-3 h-3 rounded-full flex-shrink-0 mt-0.5" :style="{ background: t.color }"></div>
                <div>
                  <p class="text-xs font-bold text-gray-900">{{ t.date }}</p>
                  <p class="text-xs text-gray-500 mt-0.5">{{ t.desc }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Guest Intelligence -->
        <div class="space-y-3">
          <h3 class="text-sm font-bold text-gray-900">Guest Intelligence</h3>

          <div v-if="guest.active_checkin" class="bg-white rounded-xl border border-gray-200 px-5 py-4">
            <p class="text-xs font-bold text-gray-900 mb-2">Current Stay Snapshot</p>
            <p class="text-xs text-gray-600">Room: {{ guest.active_checkin.room_number }}</p>
            <p class="text-xs text-gray-600">Check-in: {{ formatDate(guest.active_checkin.check_in_datetime) }}</p>
            <p class="text-xs text-gray-600">Check-out: {{ formatDate(guest.active_checkin.expected_check_out_datetime) }}</p>
            <p v-if="guest.active_checkin.total_outstanding_amount > 0" class="text-xs font-bold text-red-500 mt-1">
              Outstanding: {{ formatCurrency(guest.active_checkin.total_outstanding_amount) }}
            </p>
          </div>

          <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
            <p class="text-xs font-bold text-gray-900 mb-2">Stay History</p>
            <p class="text-xs text-gray-600">{{ guest.total_stays }} completed stays</p>
            <p class="text-xs text-gray-600">Guest type: {{ guest.guest_type }}</p>
          </div>

          <div class="bg-purple-50 rounded-xl border border-purple-100 px-5 py-4">
            <p class="text-xs font-bold text-purple-700 mb-2">Loyalty</p>
            <p class="text-xs text-purple-600">Tier: {{ guest.loyalty_tier || 'Base' }}</p>
          </div>

          <AIInsightPanel
            title="AI Guest Insight"
            context-type="guest_profile_summary"
            :context-data="aiContext"
            :auto-load="true"
            :panel-id="`guest-${guestId}`"
          />

          <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
            <p class="text-xs font-bold text-gray-900 mb-3">Quick Actions</p>
            <div class="space-y-2">
              <button @click="$router.push({ name: 'EditGuest', params: { id: guestId } })"
                class="w-full px-3 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors text-left">
                Edit Guest Profile
              </button>
              <button @click="$router.push('/guests')"
                class="w-full px-3 py-2 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
                Back to Guest List
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Stay History Tab -->
      <div v-else-if="activeTab === 'Stay History'" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">All Stays</h3>
        <div v-if="!guest.timeline || !guest.timeline.length" class="text-center py-8">
          <p class="text-xs text-gray-400">No stay history found for this guest.</p>
        </div>
        <div v-else class="space-y-3">
          <div v-for="t in guest.timeline" :key="t.date" class="flex items-start gap-3 border-b border-gray-50 pb-3">
            <div class="w-2.5 h-2.5 rounded-full flex-shrink-0 mt-1" :style="{ background: t.color }"></div>
            <div>
              <p class="text-xs font-bold text-gray-900">{{ t.date }}</p>
              <p class="text-xs text-gray-500 mt-0.5">{{ t.desc }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Other tabs placeholder -->
      <div v-else class="bg-white rounded-xl border border-gray-200 px-6 py-16 text-center">
        <p class="text-sm text-gray-400">{{ activeTab }} section coming soon</p>
      </div>

    </template>

    <!-- Document Preview Modal -->
    <Teleport to="body">
      <div v-if="showDocPreview && guest?.id_document_scan"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        style="background:rgba(15,23,42,0.75);backdrop-filter:blur(4px);"
        @click.self="showDocPreview = false">
        <div class="bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col" style="max-width:900px;width:100%;max-height:92vh;">
          <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between flex-shrink-0">
            <div>
              <p class="text-sm font-bold text-gray-900">ID Document</p>
              <p class="text-xs text-gray-400">{{ guest.id_type || '' }} {{ guest.id_number ? '• ' + guest.id_number : '' }}</p>
            </div>
            <div class="flex items-center gap-2">
              <a :href="guest.id_document_scan" download
                class="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
                Download
              </a>
              <button @click="showDocPreview = false"
                class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 text-sm">✕</button>
            </div>
          </div>
          <div class="flex-1 overflow-auto bg-gray-100 flex items-center justify-center p-4" style="min-height:400px;">
            <!-- Image -->
            <img v-if="isIdImage"
              :src="guest.id_document_scan"
              alt="ID Document"
              class="max-w-full max-h-full object-contain rounded-lg shadow" />
            <!-- PDF / other in iframe -->
            <iframe v-else
              :src="guest.id_document_scan"
              class="w-full rounded-lg"
              style="height:70vh;border:none;"
              title="ID Document Preview">
            </iframe>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { callMethodForm } from '@/lib/api'
import AIInsightPanel from '@/components/ai/AIInsightPanel.vue'

const route = useRoute()
const router = useRouter()
const guestId = route.params.id

const loading = ref(true)
const error = ref(null)
const guest = ref(null)
const showDocPreview = ref(false)

const isIdImage = computed(() => {
  const url = guest.value?.id_document_scan || ''
  return /\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i.test(url.split('?')[0])
})

const idDocFileName = computed(() => {
  const url = guest.value?.id_document_scan || ''
  return url.split('/').pop().split('?')[0] || 'document'
})

const activeTab = ref('Profile')
const tabs = ['Profile', 'Stay History', 'Spend', 'Loyalty', 'Messages']

const preferenceList = computed(() =>
  (guest.value?.preference || '')
    .split(',')
    .map(v => v.trim())
    .filter(Boolean)
)

async function fetchGuest() {
  loading.value = true
  error.value = null
  try {
    guest.value = await callMethodForm('rhohotel.rhocom_hotel.api.guest.get_guest', { name: guestId })
  } catch (e) {
    error.value = e.message || 'Failed to load guest profile.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchGuest)

function formatDate(dt) {
  if (!dt) return '—'
  const d = new Date(dt)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatCurrency(amount) {
  if (!amount) return '₦0.00'
  return '₦' + Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })
}

const palette = [
  { bg: '#dbeafe', color: '#1d4ed8' }, { bg: '#dcfce7', color: '#15803d' },
  { bg: '#fce7f3', color: '#be185d' }, { bg: '#fef9c3', color: '#a16207' },
  { bg: '#ede9fe', color: '#6d28d9' }, { bg: '#ffedd5', color: '#c2410c' },
  { bg: '#cffafe', color: '#0e7490' }, { bg: '#f1f5f9', color: '#475569' },
]
function initials(name) {
  if (!name) return '?'
  return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
}
function avatarStyle(name) {
  if (!name) return { backgroundColor: '#f1f5f9', color: '#475569' }
  const p = palette[name.charCodeAt(0) % palette.length]
  return { backgroundColor: p.bg, color: p.color }
}
function loyaltyClass(loyalty) {
  return {
    Base: 'bg-gray-100 text-gray-600', Silver: 'bg-slate-100 text-slate-600',
    Gold: 'bg-yellow-100 text-yellow-700', Platinum: 'bg-purple-100 text-purple-600',
    VIP: 'bg-orange-100 text-orange-600', Corporate: 'bg-blue-100 text-blue-600',
  }[loyalty] || 'bg-gray-100 text-gray-500'
}

const aiContext = computed(() => {
  if (!guest.value) return null
  return {
    guest_name: guest.value.hotel_guest_name,
    guest_type: guest.value.guest_type,
    loyalty_tier: guest.value.loyalty_tier || 'Base',
    total_stays: guest.value.total_stays,
    lifetime_spend: guest.value.lifetime_spend,
    nationality: guest.value.nationality,
    current_status: guest.value.current_status,
    current_room: guest.value.active_checkin?.room_number || null,
    outstanding_balance: guest.value.active_checkin?.total_outstanding_amount || 0,
  }
})
</script>
