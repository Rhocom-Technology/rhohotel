<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">{{ isEdit ? 'Edit Hall' : 'New Hall' }}</h2>
        <p class="text-xs text-gray-400 mt-0.5">{{ isEdit ? 'Update the hall profile.' : 'Complete the hall profile and publish for bookings.' }}</p>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 260px;gap:16px;align-items:start;">

      <!-- Left: Form -->
      <div class="space-y-4">

        <!-- Hall Information -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <!-- <h3 class="text-sm font-bold text-gray-900 mb-4">Hall Information</h3> -->

          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-gray-900">Hall Information</h3>

            <div class="flex gap-2">
              <button
                type="button"
                @click="showHallTypeModal = true"
                class="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50"
              >
                + Add Hall Type
              </button>

              <button
                type="button"
                @click="showHallItemModal = true"
                class="px-3 py-1.5 text-xs font-medium text-green-600 border border-green-200 rounded-lg hover:bg-green-50"
              >
                + Add Hall Item
              </button>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Hall Name <span class="text-red-500">*</span></label>
              <input v-model="form.hall_name" type="text" placeholder="e.g. Ruby Hall"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">
                Hall Type <span class="text-red-500">*</span>
              </label>

              <select
                v-model="form.hall_type"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Type</option>

                <option
                  v-for="type in hallTypes"
                  :key="type.name"
                  :value="type.name"
                >
                  {{ type.hall_type_name || type.name }}
                </option>
              </select>
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Capacity <span class="text-red-500">*</span></label>
              <input v-model="form.capacity" type="number" min="1" placeholder="e.g. 150"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Rate Per Hour <span class="text-red-500">*</span></label>
              <input v-model="form.rate_per_hour" type="number" min="0" placeholder="0"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div class="col-span-2">
              <label class="text-xs text-gray-500 mb-1 block">Hall Item</label>
              <select v-model="form.item_name"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">— select item —</option>
                <option v-for="item in allItems" :key="item.item_code" :value="item.item_code">
                  {{ item.item_name }}
                </option>
              </select>
              <p class="text-xs text-gray-400 mt-1">The ERPNext item used when generating invoices for this hall.</p>
            </div>

          </div>
        </div>

        <!-- Facilities & Setup Options -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-1">Facilities & Setup Options</h3>
          <p class="text-xs text-gray-400 mb-4">
            Select available facilities and support options for this hall.
          </p>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <label class="flex items-center gap-2 text-xs text-gray-700">
              <input type="checkbox" v-model="form.has_projector_av" />
              Projector / AV
            </label>

            <label class="flex items-center gap-2 text-xs text-gray-700">
              <input type="checkbox" v-model="form.has_sound_system" />
              Sound System
            </label>

            <label class="flex items-center gap-2 text-xs text-gray-700">
              <input type="checkbox" v-model="form.has_air_conditioning" />
              Air Conditioning
            </label>

            <label class="flex items-center gap-2 text-xs text-gray-700">
              <input type="checkbox" v-model="form.has_stage" />
              Stage
            </label>

            <label class="flex items-center gap-2 text-xs text-gray-700">
              <input type="checkbox" v-model="form.has_restroom_access" />
              Restroom Access
            </label>

            <label class="flex items-center gap-2 text-xs text-gray-700">
              <input type="checkbox" v-model="form.has_parking_access" />
              Parking Access
            </label>

            <label class="flex items-center gap-2 text-xs text-gray-700">
              <input type="checkbox" v-model="form.has_kitchen_support" />
              Kitchen Support
            </label>

            <label class="flex items-center gap-2 text-xs text-gray-700">
              <input type="checkbox" v-model="form.has_private_entrance" />
              Private Entrance
            </label>
          </div>
        </div>

        <!-- Amenities -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-sm font-bold text-gray-900">Amenities</h3>
              <p class="text-xs text-gray-400 mt-0.5">Items included with this hall.</p>
            </div>
            <button @click="addAmenity"
              class="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">+ Add Row</button>
          </div>

          <div v-if="form.amenities.length === 0" class="text-center py-6 text-xs text-gray-400">
            No amenities added yet.
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-100">
                  <th class="text-left pb-2 text-xs font-semibold text-gray-500 w-8">#</th>
                  <th class="text-left pb-2 text-xs font-semibold text-gray-500">Item</th>
                  <th class="text-left pb-2 text-xs font-semibold text-gray-500">Amenity Name</th>
                  <th class="pb-2 w-8"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="(row, i) in form.amenities" :key="i">
                  <td class="py-2 text-xs text-gray-400">{{ i + 1 }}</td>
                  <td class="py-2 pr-2">
                    <select v-model="row.item" @change="onAmenitySelect(row)"
                      class="w-full text-xs border border-gray-200 rounded px-2 py-1.5 text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500">
                      <option value="">— select —</option>
                      <option v-for="item in amenityItems" :key="item.item_code" :value="item.item_code">
                        {{ item.item_name }}
                      </option>
                    </select>
                  </td>
                  <td class="py-2 pr-2">
                    <input v-model="row.amenity_name" type="text" readonly
                      class="w-full text-xs border border-gray-100 rounded px-2 py-1.5 text-gray-600 bg-gray-50 cursor-default" />
                  </td>
                  <td class="py-2">
                    <button @click="form.amenities.splice(i, 1)"
                      class="text-red-400 hover:text-red-600 text-xs px-1">✕</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <!-- Right: Preview + Checklist + Actions -->
      <div class="space-y-4">

        <!-- Hall Preview -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Hall Preview</h3>
          <div class="bg-gray-50 rounded-lg px-4 py-3">
            <p class="text-sm font-bold text-gray-900">{{ form.hall_name || 'Hall Name' }}</p>
            <p class="text-xs text-gray-500 mt-0.5">
              {{ form.hall_type || '–' }} • {{ form.capacity ? form.capacity + ' Pax' : '–' }}
            </p>
            <p class="text-xs text-gray-500 mt-0.5">
              ₦{{ Number(form.rate_per_hour || 0).toLocaleString() }}/hr
            </p>
          </div>
          <div class="mt-3 space-y-1">
            <div v-for="a in form.amenities.filter(r => r.amenity_name)" :key="a.item"
              class="text-xs text-gray-500 flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full bg-gray-300 flex-shrink-0"></span>
              {{ a.amenity_name }}
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex gap-2">
            <router-link to="/hall" class="flex-1">
              <button class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
            </router-link>
            <button @click="createHall" :disabled="saving || !canSave"
              class="flex-1 px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              {{ saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Hall' }}
            </button>
          </div>
          <p v-if="error" class="text-xs text-red-500 mt-2">{{ error }}</p>
        </div>

      </div>
    </div>

  </div>

  <div
  v-if="showHallTypeModal"
  class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50"
>
  <div class="bg-white rounded-xl shadow-lg w-full max-w-sm p-5">
    <h3 class="text-sm font-bold text-gray-900 mb-4">Add Hall Type</h3>

    <label class="text-xs text-gray-500 mb-1 block">
      Hall Type Name <span class="text-red-500">*</span>
    </label>

    <input
      v-model="newHallTypeName"
      type="text"
      placeholder="e.g. Banquet Hall"
      class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
    />

    <p v-if="hallTypeError" class="text-xs text-red-500 mt-2">
      {{ hallTypeError }}
    </p>

    <div class="flex justify-end gap-2 mt-5">
      <button
        type="button"
        @click="closeHallTypeModal"
        class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
      >
        Cancel
      </button>

      <button
        type="button"
        @click="saveHallType"
        :disabled="savingHallType"
        class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {{ savingHallType ? 'Saving…' : 'Save' }}
      </button>
    </div>
  </div>
</div>



<div
  v-if="showHallItemModal"
  class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50"
>
  <div class="bg-white rounded-xl shadow-lg w-full max-w-sm p-5">
    <h3 class="text-sm font-bold text-gray-900 mb-4">Add Hall Item</h3>

    <label class="text-xs text-gray-500 mb-1 block">
      Hall Item Name <span class="text-red-500">*</span>
    </label>

    <input
      v-model="newHallItemName"
      type="text"
      placeholder="e.g. Ruby Hall"
      class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500"
    />

    <p class="text-xs text-gray-400 mt-1">
      This item will be created under the Hall item group.
    </p>

    <p v-if="hallItemError" class="text-xs text-red-500 mt-2">
      {{ hallItemError }}
    </p>

    <div class="flex justify-end gap-2 mt-5">
      <button
        type="button"
        @click="closeHallItemModal"
        class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
      >
        Cancel
      </button>

      <button
        type="button"
        @click="saveHallItem"
        :disabled="savingHallItem"
        class="px-4 py-2 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50"
      >
        {{ savingHallItem ? 'Saving…' : 'Save' }}
      </button>
    </div>
  </div>
</div>

</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { callMethod } from '@/lib/api'

const router  = useRouter()
const route   = useRoute()
const isEdit  = computed(() => !!route.params.id)
const saving  = ref(false)
const error   = ref(null)
const allItems    = ref([]) 
const amenityItems = ref([]) 
const hallTypes    = ref([])
const showHallTypeModal = ref(false)
const newHallTypeName = ref('')
const savingHallType = ref(false)
const hallTypeError = ref(null)

const showHallItemModal = ref(false)
const newHallItemName = ref('')
const savingHallItem = ref(false)
const hallItemError = ref(null)

const form = ref({
  hall_name: '',
  hall_type: '',
  capacity: '',
  rate_per_hour: '',
  item_name: '',
  amenities: [],

  has_projector_av: false,
  has_sound_system: false,
  has_air_conditioning: false,
  has_stage: false,
  has_restroom_access: false,
  has_parking_access: false,
  has_kitchen_support: false,
  has_private_entrance: false,
})

const canSave = computed(() =>
  !!(form.value.hall_name && form.value.hall_type && form.value.capacity && form.value.rate_per_hour)
)

function addAmenity() {
  form.value.amenities.push({ item: '', amenity_name: '' })
}

function onAmenitySelect(row) {
  const found = amenityItems.value.find(i => i.item_code === row.item)
  if (found) row.amenity_name = found.item_name
  else row.amenity_name = ''
}

function closeHallTypeModal() {
  showHallTypeModal.value = false
  newHallTypeName.value = ''
  hallTypeError.value = null
}

async function saveHallType() {
  if (!newHallTypeName.value.trim()) {
    hallTypeError.value = 'Hall Type Name is required.'
    return
  }

  savingHallType.value = true
  hallTypeError.value = null

  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.hall.create_hall_type', {
      hall_type_name: newHallTypeName.value.trim()
    })

    hallTypes.value.push(result)
    form.value.hall_type = result.name

    closeHallTypeModal()
  } catch (e) {
    hallTypeError.value = e.message || 'Failed to create hall type.'
  } finally {
    savingHallType.value = false
  }
}

function closeHallItemModal() {
  showHallItemModal.value = false
  newHallItemName.value = ''
  hallItemError.value = null
}

async function saveHallItem() {
  if (!newHallItemName.value.trim()) {
    hallItemError.value = 'Hall Item Name is required.'
    return
  }

  savingHallItem.value = true
  hallItemError.value = null

  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.hall.create_hall_item', {
      item_name: newHallItemName.value.trim()
    })

    allItems.value.push(result)
    form.value.item_name = result.item_code

    closeHallItemModal()
  } catch (e) {
    hallItemError.value = e.message || 'Failed to create hall item.'
  } finally {
    savingHallItem.value = false
  }
}


async function createHall() {
  if (!canSave.value) return
  saving.value = true
  error.value  = null
  try {
   const payload = JSON.stringify({
      hall_name: form.value.hall_name,
      hall_type: form.value.hall_type,
      capacity: form.value.capacity,
      rate_per_hour: form.value.rate_per_hour,
      item_name: form.value.item_name,
      amenities: form.value.amenities.filter(a => a.item),

      has_projector_av: form.value.has_projector_av,
      has_sound_system: form.value.has_sound_system,
      has_air_conditioning: form.value.has_air_conditioning,
      has_stage: form.value.has_stage,
      has_restroom_access: form.value.has_restroom_access,
      has_parking_access: form.value.has_parking_access,
      has_kitchen_support: form.value.has_kitchen_support,
      has_private_entrance: form.value.has_private_entrance,
    })
    if (isEdit.value) {
      await callMethod('rhohotel.rhocom_hotel.api.hall.update_hall', {
        name: route.params.id,
        data: payload,
      })
      router.push(`/hall/${route.params.id}`)
    } else {
      const result = await callMethod('rhohotel.rhocom_hotel.api.hall.create_hall', { data: payload })
      router.push(`/hall/${result.name}`)
    }
  } catch (e) {
    error.value = e.message || 'Failed to save hall.'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const calls = [
      callMethod('rhohotel.rhocom_hotel.api.hall.get_all_items'),
      callMethod('rhohotel.rhocom_hotel.api.hall.get_amenity_items'),
      callMethod('rhohotel.rhocom_hotel.api.hall.get_hall_types'),
    ]
    if (route.params.id) {
      calls.push(callMethod('rhohotel.rhocom_hotel.api.hall.get_hall', { name: route.params.id }))
    }
    const results = await Promise.all(calls)
   allItems.value     = results[0] || []
  amenityItems.value = results[1] || []
  hallTypes.value    = results[2] || []
  const existing     = results[3]

    if (existing) {
      form.value.hall_name = existing.hall_name || ''
      form.value.hall_type = existing.hall_type || ''
      form.value.capacity = existing.capacity || ''
      form.value.rate_per_hour = existing.rate_per_hour || ''
      form.value.item_name = existing.item_name || ''
      form.value.amenities = (existing.amenities || []).map(a => ({
        item: a.item || '',
        amenity_name: a.amenity_name || '',
      }))

      form.value.has_projector_av = !!existing.has_projector_av
      form.value.has_sound_system = !!existing.has_sound_system
      form.value.has_air_conditioning = !!existing.has_air_conditioning
      form.value.has_stage = !!existing.has_stage
      form.value.has_restroom_access = !!existing.has_restroom_access
      form.value.has_parking_access = !!existing.has_parking_access
      form.value.has_kitchen_support = !!existing.has_kitchen_support
      form.value.has_private_entrance = !!existing.has_private_entrance
    }


  } catch (e) {
    console.error('Failed to load', e)
  }
})
</script>