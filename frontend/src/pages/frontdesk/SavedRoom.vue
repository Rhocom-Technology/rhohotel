<template>
  <div class="space-y-5">

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- Error -->
    <div v-else-if="loadError" class="bg-red-50 border border-red-200 rounded-xl px-6 py-10 text-center">
      <p class="text-sm font-semibold text-red-500 mb-2">{{ loadError }}</p>
      <button @click="loadRoom" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Retry</button>
    </div>

    <template v-else-if="room">

    <!-- Room Record Summary Bar -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Room Record Summary</h3>
        <p class="text-xs text-gray-400 mt-0.5">
          Room {{ room.room_number }} • {{ room.room_type }} • Floor {{ room.floor }} •
          {{ room.occupancy === 'Occupied' ? 'occupied and linked to active check-in record' : room.occupancy.toLowerCase() }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/rooms')">Room List</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Print</button>
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Block Room</button>
        <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">Edit Room</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Base Rate</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">{{ room.rate_plan || 'BAR' }}</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ formatCurrency(room.rate) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Current Guest</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full"
            :class="room.guest_name ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'">
            {{ room.guest_name ? 'In House' : 'Vacant' }}
          </span>
        </div>
        <p class="text-xl font-bold text-gray-900 mt-1">{{ room.guest_name || '—' }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Current Check-in ID</p>
          <span class="px-2.5 py-0.5 text-xs font-medium rounded-full"
            :class="room.current_check_in ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400'">
            {{ room.current_check_in ? 'Linked' : 'None' }}
          </span>
        </div>
        <p class="text-base font-bold text-gray-900 mt-1">{{ room.current_check_in || '—' }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Housekeeping Default</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Status</span>
        </div>
        <p class="text-xl font-bold text-gray-900 mt-1">{{ room.housekeeping_status || '—' }}</p>
      </div>
    </div>

    <!-- Details + Operational Setup -->
    <div style="display:grid;grid-template-columns:1fr 320px;gap:12px;">

      <!-- Room Details -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-5">Room Details</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Number</p>
            <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ room.room_number }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Floor</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ room.floor || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ room.room_type || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Bed Type</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ room.bed_type || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Current Guest</p>
            <div class="px-3 py-2.5 text-xs font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg">{{ room.guest_name || '—' }}</div>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Current Check-in ID</p>
            <div class="px-3 py-2.5 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">{{ room.current_check_in || '—' }}</div>
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Room Description</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg leading-relaxed min-h-16">
            {{ room.description || 'No description provided.' }}
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Operational Notes</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg leading-relaxed min-h-16">
            {{ room.operational_notes || 'No operational notes.' }}
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-1.5">Amenities / Features</p>
          <div class="px-3 py-3 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg">
            {{ room.amenities && room.amenities.length ? room.amenities.join(' • ') : '—' }}
          </div>
        </div>
      </div>

      <!-- Operational Setup -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-4">
        <h3 class="text-sm font-bold text-gray-900">Operational Setup</h3>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Room Status</p>
          <div class="px-3 py-2.5 text-xs font-semibold bg-gray-50 border border-gray-200 rounded-lg"
            :class="occupancyClass(room.occupancy)">
            {{ room.occupancy }}
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Keycard Enabled</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
            <label class="flex items-center gap-2.5">
              <input type="checkbox" :checked="room.keycard_enabled" disabled class="accent-blue-600 w-3.5 h-3.5" />
              <span class="text-xs text-gray-700">{{ room.keycard_enabled ? 'Yes, keycard activation allowed' : 'Keycard not enabled' }}</span>
            </label>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Maintenance Block</p>
          <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
            <label class="flex items-center gap-2.5">
              <input type="checkbox" :checked="room.maintenance_flag" disabled class="accent-blue-600 w-3.5 h-3.5" />
              <span class="text-xs text-gray-700">Out of service flag active</span>
            </label>
            <label class="flex items-center gap-2.5">
              <input type="checkbox" :checked="room.require_inspection" disabled class="accent-blue-600 w-3.5 h-3.5" />
              <span class="text-xs text-gray-700">Require inspection before release</span>
            </label>
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-1.5">Inventory Status</p>
          <div class="px-4 py-2.5 text-xs font-semibold rounded-lg"
            :class="room.occupancy === 'Occupied' ? 'text-yellow-700 bg-yellow-50 border border-yellow-200' :
                    room.occupancy === 'Vacant'   ? 'text-blue-700 bg-blue-50 border border-blue-200' :
                    'text-red-700 bg-red-50 border border-red-200'">
            {{ room.occupancy === 'Occupied' ? 'Occupied and linked to active stay' :
               room.occupancy === 'Vacant'   ? 'Vacant and available' :
               'Out of service' }}
          </div>
        </div>

        <div>
          <p class="text-xs text-gray-500 mb-2">Audit Trail</p>
          <div class="bg-gray-50 rounded-xl border border-gray-200 px-4 py-3 space-y-3">
            <div v-for="a in room.audit" :key="a.time">
              <p class="text-xs font-semibold text-gray-900">{{ a.time }}</p>
              <p class="text-xs text-gray-500">{{ a.action }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const room = ref(null)
const loading = ref(true)
const loadError = ref('')

function formatCurrency(val) {
  if (!val) return '₦0'
  return `₦${Number(val).toLocaleString('en-NG', { minimumFractionDigits: 0 })}`
}

function occupancyClass(o) {
  return {
    'Occupied':    'text-green-600',
    'Vacant':      'text-blue-600',
    'Unavailable': 'text-red-500',
  }[o] || 'text-gray-600'
}

async function loadRoom() {
  loading.value = true
  loadError.value = ''
  try {
    const body = new URLSearchParams({ room_id: route.params.id })
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.room.get_room_detail', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Frappe-CSRF-Token': window.csrf_token || '',
      },
      body: body.toString(),
    })
    const data = await res.json()
    if (data.exc) {
      loadError.value = 'Failed to load room details.'
    } else {
      room.value = data.message
    }
  } catch (e) {
    loadError.value = 'Network error — please check connection.'
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadRoom)
</script>