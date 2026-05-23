<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Technician Register Control</h2>
        <p class="text-xs text-gray-400 mt-0.5">Track technician type, specialization, assignment availability, response performance, and preferred service source.</p>
      </div>
      <div class="flex items-center gap-3">
        <button @click="router.push('/maintenance/new-technician')"
          class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">
          New Technician
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center h-48 gap-3">
      <svg class="animate-spin w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
      </svg>
      <p class="text-sm text-gray-400">Loading technicians...</p>
    </div>

    <template v-else>

      <!-- Stats -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">Total Technicians</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Live</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.total }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">In-House Employees</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Internal</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.in_house }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">Outsourced</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">External</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.outsourced }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-xs text-gray-400">Available Now</p>
            <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Ready</span>
          </div>
          <p class="text-3xl font-bold text-gray-900">{{ stats.available }}</p>
        </div>
      </div>

      <!-- Filters -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4">
        <h3 class="text-sm font-bold text-gray-900 mb-3">Filters & Search</h3>
        <div class="flex items-center gap-3 flex-wrap">
          <div class="relative" style="flex:1;min-width:180px;">
            <input v-model="search" type="text" placeholder="Search name, skill, phone, vendor..."
              class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <select v-model="filterType" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
            <option value="">All Types</option>
            <option value="In-House">In-House</option>
            <option value="Outsourced">Outsourced</option>
          </select>
          <select v-model="filterSpec" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
            <option value="">All Specializations</option>
            <option value="Laundry / Mechanical">Laundry / Mechanical</option>
            <option value="Boiler / Heating">Boiler / Heating</option>
            <option value="Electrical / Electronics">Electrical / Electronics</option>
            <option value="HVAC">HVAC</option>
            <option value="TV / Smart Lock / IT">TV / Smart Lock / IT</option>
            <option value="Plumbing / Pump">Plumbing / Pump</option>
            <option value="General Maintenance">General Maintenance</option>
          </select>
          <select v-model="filterAvail" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
            <option value="">All Availability</option>
            <option value="Available">Available</option>
            <option value="On Call">On Call</option>
            <option value="Unavailable">Unavailable</option>
          </select>
          <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
          <button @click="filterAvail = 'Available'" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Available Only</button>
        </div>
      </div>

      <!-- Table -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900">Technician Records</h3>
          <p class="text-xs text-gray-400">
            Showing {{ ((page - 1) * pageSize) + 1 }}–{{ Math.min(page * pageSize, filteredList.length) }} of {{ filteredList.length }}
          </p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-semibold text-gray-400 px-6 py-3">Technician ID</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Name</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Type</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Specialization</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Contact</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Source / Vendor</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Open Tasks</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Availability</th>
                <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="t in paginatedList" :key="t.name"
                class="hover:bg-gray-50 transition-colors cursor-pointer"
                @click="router.push({ name: 'TechnicianView', params: { id: t.name } })">
                <td class="px-6 py-4 text-xs font-bold text-gray-900 font-mono">{{ t.name }}</td>
                <td class="px-4 py-4">
                  <p class="text-xs font-semibold text-gray-900">{{ t.technician_name }}</p>
                  <p class="text-xs text-gray-400 mt-0.5">
                    {{ t.technician_type === 'In-House' ? 'In-house technician' : 'External contractor' }}
                  </p>
                </td>
                <td class="px-4 py-4">
                  <span class="px-2.5 py-1 text-xs font-semibold rounded-full"
                    :class="t.technician_type === 'In-House' ? 'bg-blue-100 text-blue-600' : 'bg-orange-100 text-orange-600'">
                    {{ t.technician_type }}
                  </span>
                </td>
                <td class="px-4 py-4 text-xs text-gray-600">{{ t.primary_specialization || '—' }}</td>
                <td class="px-4 py-4 text-xs text-gray-600">{{ t.phone || '—' }}</td>
                <td class="px-4 py-4 text-xs text-gray-600">{{ t.source_label }}</td>
                <td class="px-4 py-4">
                  <span class="text-xs font-semibold" :class="t.open_tasks_count > 0 ? 'text-blue-600' : 'text-gray-400'">
                    {{ t.open_tasks_count }}
                  </span>
                </td>
                <td class="px-4 py-4">
                  <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="availClass(t.availability)">
                    {{ t.availability }}
                  </span>
                </td>
                <td class="px-4 py-4">
                  <button
                    @click.stop="router.push({ name: 'TechnicianView', params: { id: t.name } })"
                    class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
                    View
                  </button>
                </td>
              </tr>
              <tr v-if="filteredList.length === 0">
                <td colspan="9" class="text-center py-10 text-xs text-gray-400">No technicians found</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <p class="text-xs text-gray-400">Rows per page:</p>
            <select v-model="pageSize" @change="page = 1" class="text-xs border border-gray-200 rounded-lg px-2 py-1">
              <option :value="10">10</option>
              <option :value="25">25</option>
              <option :value="50">50</option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <button @click="page--" :disabled="page === 1"
              class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
              Previous
            </button>
            <span class="text-xs text-gray-600">Page {{ page }} of {{ totalPages }}</span>
            <button @click="page++" :disabled="page === totalPages"
              class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40">
              Next
            </button>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const loading = ref(true)
const technicians = ref([])
const stats = ref({ total: 0, in_house: 0, outsourced: 0, available: 0 })

const search = ref('')
const filterType = ref('')
const filterSpec = ref('')
const filterAvail = ref('')
const page = ref(1)
const pageSize = ref(25)

// ─── Fetch ────────────────────────────────────────────────────────────────────
const listResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.technician.get_technicians_list',
  auto: false
})

async function loadList() {
  loading.value = true
  try {
    const res = await listResource.fetch()
    console.log('[TechnicianList] get_technicians_list:', res)
    technicians.value = res?.technicians || []
    stats.value = res?.stats || { total: 0, in_house: 0, outsourced: 0, available: 0 }
  } catch (e) {
    console.error('[TechnicianList] error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadList)

// ─── Filter + paginate ────────────────────────────────────────────────────────
const filteredList = computed(() => {
  let list = technicians.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(t =>
      t.technician_name?.toLowerCase().includes(q) ||
      t.primary_specialization?.toLowerCase().includes(q) ||
      t.phone?.includes(q) ||
      t.source_label?.toLowerCase().includes(q)
    )
  }
  if (filterType.value) list = list.filter(t => t.technician_type === filterType.value)
  if (filterSpec.value) list = list.filter(t => t.primary_specialization === filterSpec.value)
  if (filterAvail.value) list = list.filter(t => t.availability === filterAvail.value)
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredList.value.length / pageSize.value)))
const paginatedList = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredList.value.slice(start, start + pageSize.value)
})

// Reset page on filter change
watch([search, filterType, filterSpec, filterAvail, pageSize], () => { page.value = 1 })

function clearFilters() {
  search.value = ''
  filterType.value = ''
  filterSpec.value = ''
  filterAvail.value = ''
  page.value = 1
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function availClass(a) {
  return {
    'Available':   'bg-green-100 text-green-600',
    'On Call':     'bg-yellow-100 text-yellow-600',
    'Unavailable': 'bg-red-100 text-red-500',
  }[a] || 'bg-gray-100 text-gray-500'
}
</script>