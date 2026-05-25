<template>
  <!-- Inline guest selector: shows current value, opens dropdown/create panel on click -->
  <div class="relative w-full" ref="root">
    <!-- Display row -->
    <div
      class="flex items-center gap-2 group cursor-pointer w-full min-h-[38px] px-3 py-2.5 text-sm border border-gray-200 rounded-lg bg-white"
      @click="toggleOpen"
    >
      <span class="text-sm text-gray-700 truncate w-full">{{ displayValue || 'Select guest' }}</span>
      <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    </div>

    <!-- Dropdown panel – teleported to body to escape overflow:hidden/auto containers -->
    <Teleport to="body">
      <div
        v-if="open"
        ref="dropdown"
        class="fixed z-[9999] bg-white border border-gray-200 rounded-xl shadow-xl"
        :style="dropdownStyle"
      >
      <!-- Search existing -->
      <div class="p-2 border-b border-gray-100">
        <input
          ref="searchInput"
          v-model="query"
          type="text"
          placeholder="Search guests…"
          class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          @input="onSearch"
        />
      </div>

      <!-- Results list -->
      <div class="max-h-48 overflow-y-auto">
        <div v-if="searching" class="px-4 py-3 text-xs text-gray-400 text-center">Searching…</div>
        <div v-else-if="results.length === 0 && query.length > 0" class="px-4 py-3 text-xs text-gray-400 text-center">No guests found.</div>
        <button
          v-for="g in results"
          :key="g.name"
          class="w-full text-left px-4 py-2.5 text-xs hover:bg-blue-50 flex flex-col"
          @mousedown.prevent="selectGuest(g)"
        >
          <span class="font-medium text-gray-800">{{ g.hotel_guest_name }}</span>
          <span class="text-gray-400">{{ g.email || g.phone_number || '' }}</span>
        </button>
      </div>

      <!-- Create new guest toggle -->
      <div class="border-t border-gray-100 p-2">
        <button
          class="w-full text-xs text-blue-600 font-semibold px-3 py-2 rounded-lg hover:bg-blue-50 text-left"
          @click="showCreate = !showCreate"
        >
          {{ showCreate ? '— Cancel new guest' : '+ Create new guest' }}
        </button>

        <!-- New guest mini-form -->
        <div v-if="showCreate" class="mt-2 space-y-2 px-1 pb-1">
          <input v-model="newGuest.hotel_guest_name" type="text" placeholder="Full name *"
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <input v-model="newGuest.email" type="email" placeholder="Email"
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <input v-model="newGuest.phone_number" type="tel" placeholder="Phone"
            class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <p v-if="createError" class="text-xs text-red-500">{{ createError }}</p>
          <button
            :disabled="!newGuest.hotel_guest_name || creating"
            @click="createGuest"
            class="w-full px-3 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {{ creating ? 'Saving…' : 'Save & Select' }}
          </button>
        </div>
      </div>
    </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { callMethod } from '@/lib/api'

const props = defineProps({
  modelValue: { type: String, default: '' },   // guest_name (display name stored on row)
  guestId: { type: String, default: '' },       // hotel_guest docname if available
  fallbackValue: { type: String, default: '' },
  guestType: { type: String, default: 'Individual' },
})
const emit = defineEmits(['update:modelValue', 'update:guestId', 'selected'])

const root = ref(null)
const dropdown = ref(null)
const searchInput = ref(null)
const open = ref(false)
const dropdownStyle = ref({})

function updateDropdownPosition() {
  if (!root.value) return
  const rect = root.value.getBoundingClientRect()
  dropdownStyle.value = {
    top: `${rect.bottom + window.scrollY + 4}px`,
    left: `${rect.left + window.scrollX}px`,
    minWidth: '280px',
  }
}

function toggleOpen() {
  if (!open.value) updateDropdownPosition()
  open.value = !open.value
}
const query = ref('')
const results = ref([])
const searching = ref(false)
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const newGuest = ref({ hotel_guest_name: '', email: '', phone_number: '', guest_type: 'Individual' })

const displayValue = computed(() => props.modelValue || props.fallbackValue || '')

let searchTimer = null
function onSearch() {
  clearTimeout(searchTimer)
  if (query.value.length < 1) { results.value = []; return }
  searchTimer = setTimeout(searchGuests, 300)
}

async function searchGuests() {
  searching.value = true
  try {
    const rows = await callMethod('frappe.client.get_list', {
      doctype: 'Hotel Guest',
      fields: ['name', 'hotel_guest_name', 'email', 'phone_number', 'customer'],
      filters: [
        ['guest_type', '=', props.guestType || 'Individual'],
        ['hotel_guest_name', 'like', `%${query.value}%`],
      ],
      limit_page_length: 20,
    })
    results.value = rows || []
  } catch {
    results.value = []
  } finally {
    searching.value = false
  }
}

function selectGuest(g) {
  emit('update:modelValue', g.hotel_guest_name)
  emit('update:guestId', g.name)
  emit('selected', g)
  open.value = false
  query.value = ''
  results.value = []
}

async function createGuest() {
  if (!newGuest.value.hotel_guest_name) return
  creating.value = true
  createError.value = ''
  try {
    const doc = await callMethod('frappe.client.insert', {
      doc: {
        doctype: 'Hotel Guest',
        hotel_guest_name: newGuest.value.hotel_guest_name,
        email: newGuest.value.email || '',
        phone_number: newGuest.value.phone_number || '',
        guest_type: props.guestType || 'Individual',
      },
    })
    selectGuest({
      name: doc.name,
      hotel_guest_name: doc.hotel_guest_name || newGuest.value.hotel_guest_name,
      email: doc.email || newGuest.value.email || '',
      phone_number: doc.phone_number || newGuest.value.phone_number || '',
      customer: doc.customer || '',
    })
    newGuest.value = { hotel_guest_name: '', email: '', phone_number: '', guest_type: 'Individual' }
    showCreate.value = false
  } catch (e) {
    createError.value = e?.message || 'Failed to create guest.'
  } finally {
    creating.value = false
  }
}

// Open search input when dropdown opens
watch(open, async (val) => {
  if (val) {
    await nextTick()
    searchInput.value?.focus()
    if (!query.value) await searchGuests()
  }
})

// Close on outside click
function onClickOutside(e) {
  const clickedRoot = root.value?.contains(e.target)
  const clickedDropdown = dropdown.value?.contains(e.target)
  if (!clickedRoot && !clickedDropdown) open.value = false
}
onMounted(() => document.addEventListener('mousedown', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', onClickOutside))

// Populate initial search when empty
onMounted(async () => {
  try {
    const rows = await callMethod('frappe.client.get_list', {
      doctype: 'Hotel Guest',
      fields: ['name', 'hotel_guest_name', 'email', 'phone_number', 'customer'],
      filters: [['guest_type', '=', props.guestType || 'Individual']],
      limit_page_length: 20,
    })
    results.value = rows || []
  } catch { results.value = [] }
})
</script>
