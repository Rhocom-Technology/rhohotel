<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">Front desk • create room inventory record and operational setup</p>
    </div>

    <!-- Control Bar -->
    <div class="bg-white rounded-xl border-2 border-blue-400 px-6 py-4 flex items-center justify-between">
      <div>
        <h3 class="text-sm font-bold text-gray-900">Create Room Record</h3>
        <p class="text-xs text-gray-400 mt-0.5">Enter room identity, category, pricing, floor location, occupancy setup, and operational controls.</p>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="$router.push('/rooms')">Cancel</button>
        <button :disabled="saving" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 transition-colors"
          @click="saveRoom">{{ saving ? 'Saving…' : 'Save Room' }}</button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="bg-red-50 border border-red-200 rounded-xl px-5 py-3 text-xs text-red-600">{{ errorMsg }}</div>

    <div style="display:grid;grid-template-columns:1fr 300px;gap:12px;">

      <!-- Room Details -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Room Details</h3>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;" class="mb-4">
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Number <span class="text-red-400">*</span></p>
            <input type="text" v-model="form.room_number" placeholder="Enter room number"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Floor <span class="text-red-400">*</span></p>
            <select v-model="form.floor" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option value="">Select floor</option>
              <option v-for="f in floorOptions" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Type <span class="text-red-400">*</span></p>
            <select v-model="form.room_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option value="">Select room type</option>
              <option v-for="rt in roomTypeOptions" :key="rt" :value="rt">{{ rt }}</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Bed Type</p>
            <select v-model="form.bed_type" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option value="">Select bed type</option>
              <option>1 King Bed</option>
              <option>1 Queen Bed</option>
              <option>2 Twin Beds</option>
              <option>1 Double Bed</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Base Rate</p>
            <input type="number" v-model.number="form.base_rate" placeholder="₦0.00" min="0"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Capacity (Adults)</p>
            <input type="number" v-model.number="form.capacity" min="1" placeholder="1"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Rate Plan</p>
            <select v-model="form.rate_plan" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>Standard BAR</option>
              <option>Corporate Rate</option>
              <option>Promotional</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Status</p>
            <select v-model="form.status" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>Vacant</option>
              <option>Occupied</option>
              <option>Reserved</option>
              <option>Maintenance</option>
            </select>
          </div>
        </div>

        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Room Description</p>
          <textarea v-model="form.description" rows="3"
            placeholder="Enter room overview, style, furnishing notes, and guest-facing description..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
        </div>
        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1.5">Operational Notes</p>
          <textarea v-model="form.operational_notes" rows="3"
            placeholder="Maintenance note, inspection rule, or setup note for operations..."
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1.5">Phone Extension</p>
          <input type="text" v-model="form.phone" placeholder="e.g. 201"
            class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
      </div>

      <!-- Room Setup -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5 space-y-4">
          <h3 class="text-sm font-bold text-gray-900">Room Setup</h3>

          <div>
            <p class="text-xs text-gray-500 mb-1.5">Housekeeping Default</p>
            <select v-model="form.housekeeping_status" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>Clean</option>
              <option>Dirty</option>
              <option>Inspected</option>
              <option>In Progress</option>
            </select>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-1.5">Operational Status</p>
            <select v-model="form.operational_status" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>In Service</option>
              <option>Out of Service</option>
              <option>Blocked</option>
            </select>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-2">Keycard Enabled</p>
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3">
              <label class="flex items-center gap-2.5 cursor-pointer">
                <input type="checkbox" v-model="form.keycard_enabled" class="accent-blue-600 w-3.5 h-3.5" />
                <span class="text-xs text-gray-700">Allow keycard activation for this room</span>
              </label>
            </div>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-2">Maintenance Block</p>
            <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
              <label class="flex items-center gap-2.5 cursor-pointer">
                <input type="checkbox" v-model="form.maintenance_flag" class="accent-blue-600 w-3.5 h-3.5" />
                <span class="text-xs text-gray-700">Mark room as out of service on save</span>
              </label>
              <label class="flex items-center gap-2.5 cursor-pointer">
                <input type="checkbox" v-model="form.require_inspection" class="accent-blue-600 w-3.5 h-3.5" />
                <span class="text-xs text-gray-700">Require inspection before release</span>
              </label>
            </div>
          </div>

          <div>
            <p class="text-xs text-gray-500 mb-1.5">Room Classification</p>
            <select v-model="form.classification" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
              <option>Sellable Room</option>
              <option>Complimentary Room</option>
              <option>Staff Room</option>
              <option>Storage</option>
            </select>
          </div>
        </div>

        <!-- Preview Summary -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
          <p class="text-xs text-gray-500 mb-2">Preview Summary</p>
          <div class="bg-blue-50 rounded-xl border border-blue-200 px-4 py-4">
            <p class="text-sm font-bold text-blue-700 mb-2">New Room Preview</p>
            <p class="text-xs text-blue-600">Room No: {{ form.room_number || '—' }}</p>
            <p class="text-xs text-blue-600">Type: {{ form.room_type || '—' }}</p>
            <p class="text-xs text-blue-600">Rate: {{ form.base_rate ? '₦' + Number(form.base_rate).toLocaleString() : '₦0.00' }}</p>
            <p class="text-xs text-blue-600">Status: {{ form.status }}</p>
          </div>
        </div>

        <!-- Quick Tips -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
          <p class="text-xs text-gray-500 mb-2">Quick Tips</p>
          <div class="bg-gray-50 rounded-xl border border-gray-200 px-4 py-3">
            <p class="text-xs text-gray-500 leading-relaxed">Use unique room number, correct floor, and room type before saving to keep inventory clean.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer note -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-3">
      <p class="text-xs text-gray-400">New room setup page for room inventory, pricing, and operational configuration.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const saving = ref(false)
const errorMsg = ref('')
const roomTypeOptions = ref([])
const floorOptions = ref([])

const form = reactive({
  room_number: '',
  floor: '',
  room_type: '',
  bed_type: '',
  base_rate: 0,
  capacity: 1,
  extra_bed_capacity: 0,
  rate_plan: 'Standard BAR',
  status: 'Vacant',
  operational_status: 'In Service',
  housekeeping_status: 'Clean',
  phone: '',
  description: '',
  operational_notes: '',
  keycard_enabled: true,
  maintenance_flag: false,
  require_inspection: false,
  classification: 'Sellable Room',
})

onMounted(async () => {
  try {
    const res = await fetch('/api/method/rhohotel.rhocom_hotel.api.room.get_room_inventory', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Frappe-CSRF-Token': window.csrf_token || ''
      }
    })
    const data = await res.json()
    const msg = data.message || {}
    roomTypeOptions.value = msg.room_types || []
    floorOptions.value = msg.floors || []
  } catch (e) {
    console.error('Failed to load options', e)
  }
})

async function saveRoom() {
  errorMsg.value = ''
  if (!form.room_number) { errorMsg.value = 'Room number is required.'; return }
  if (!form.room_type) { errorMsg.value = 'Room type is required.'; return }
  if (!form.floor) { errorMsg.value = 'Floor is required.'; return }

  saving.value = true
  try {
    const res = await fetch('/api/method/frappe.client.insert', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Frappe-CSRF-Token': window.csrf_token || ''
      },
      body: new URLSearchParams({
        doc: JSON.stringify({
          doctype: 'Hotel Room',
          room_number: form.room_number,
          floor: form.floor,
          room_type: form.room_type,
          bed_type: form.bed_type,
          base_rate: form.base_rate,
          capacity: form.capacity,
          extra_bed_capacity: form.extra_bed_capacity,
          rate_plan: form.rate_plan,
          status: form.status,
          operational_status: form.operational_status,
          housekeeping_status: form.housekeeping_status,
          phone: form.phone,
          description: form.description,
          operational_notes: form.operational_notes,
          keycard_enabled: form.keycard_enabled ? 1 : 0,
          maintenance_flag: form.maintenance_flag ? 1 : 0,
          require_inspection: form.require_inspection ? 1 : 0,
          classification: form.classification,
        })
      })
    })
    const data = await res.json()
    if (data.exc) {
      try {
        errorMsg.value = JSON.parse(JSON.parse(data._server_messages || '[]')[0]).message
      } catch {
        errorMsg.value = 'Could not save room.'
      }
    } else {
      router.push('/rooms/' + (data.message?.name || form.room_number))
    }
  } catch (e) {
    errorMsg.value = 'Network error. Please try again.'
    console.error(e)
  } finally {
    saving.value = false
  }
}
</script>
