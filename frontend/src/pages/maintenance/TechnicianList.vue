<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Technician Register Control</h2>
        <p class="text-xs text-gray-400 mt-0.5">Track technician type, specialization, assignment availability, response performance, and preferred service source.</p>
      </div>
      <div class="flex items-center gap-3">
        <button class="px-4 py-2 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">Export List</button>
        <button @click="router.push('/maintenance/new-technician')" class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600">New Technician</button>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Total Technicians</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">Live</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">46</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">In-House Employees</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Internal</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">28</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Outsourced Technicians</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-600 rounded-full">External</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">18</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-xs text-gray-400">Available Now</p>
          <span class="px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-600 rounded-full">Ready</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">31</p>
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
        </select>
        <select v-model="filterAvail" class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none">
          <option value="">All Availability</option>
          <option value="Available">Available</option>
          <option value="On Call">On Call</option>
          <option value="Unavailable">Unavailable</option>
          <option value="Booked">Booked</option>
        </select>
        <button @click="clearFilters" class="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Reset</button>
        <button @click="filterAvail = 'Available'" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Show Available Only</button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-100">
        <h3 class="text-sm font-bold text-gray-900">Technician Records</h3>
        <p class="text-xs text-gray-400">Showing 1–{{ filteredList.length }} of 46 technicians</p>
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
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Availability</th>
              <th class="text-left text-xs font-semibold text-gray-400 px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="t in filteredList" :key="t.id" class="hover:bg-gray-50 transition-colors cursor-pointer" @click="viewTechnician(t)">
              <td class="px-6 py-4 text-xs font-bold text-gray-900">{{ t.id }}</td>
              <td class="px-4 py-4">
                <p class="text-xs font-semibold text-gray-900">{{ t.name }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ t.subtitle }}</p>
              </td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ t.type }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ t.specialization }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ t.contact }}</td>
              <td class="px-4 py-4 text-xs text-gray-600">{{ t.source }}</td>
              <td class="px-4 py-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="availClass(t.availability)">{{ t.availability }}</span>
              </td>
              <td class="px-4 py-4">
                <button @click.stop="viewTechnician(t)" class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">View</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
        <p class="text-xs text-gray-400">Rows per page: 25</p>
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1">
            <button class="w-6 h-6 text-xs rounded bg-blue-600 text-white flex items-center justify-center">1</button>
            <button class="w-6 h-6 text-xs rounded text-gray-500 hover:bg-gray-100 flex items-center justify-center">2</button>
          </div>
          <button class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Next</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const search = ref('')
const filterType = ref('')
const filterSpec = ref('')
const filterAvail = ref('')

const technicians = [
  { id: 'TECH-00041', name: 'Engr. Paul Okoro', subtitle: 'Senior maintenance technician', type: 'In-House', specialization: 'Laundry / Mechanical', contact: '+234 803 222 1180', source: 'Employee', availability: 'Available' },
  { id: 'TECH-00042', name: 'HeatPro Boiler Services', subtitle: 'External boiler specialist', type: 'Outsourced', specialization: 'Boiler / Heating', contact: '+234 809 888 4400', source: 'HeatPro Ltd', availability: 'On Call' },
  { id: 'TECH-00043', name: 'Musa Ibrahim', subtitle: 'Electrical technician', type: 'In-House', specialization: 'Electrical / Electronics', contact: '+234 814 117 9022', source: 'Employee', availability: 'Unavailable' },
  { id: 'TECH-00044', name: 'CoolAir Systems', subtitle: 'HVAC contractor', type: 'Outsourced', specialization: 'HVAC', contact: '+234 802 777 0191', source: 'CoolAir Systems', availability: 'Booked' },
  { id: 'TECH-00045', name: 'Amina Yusuf', subtitle: 'Room electronics technician', type: 'In-House', specialization: 'TV / Smart Lock / IT', contact: '+234 816 440 8812', source: 'Employee', availability: 'Available' },
  { id: 'TECH-00046', name: 'Prime Water Works', subtitle: 'Plumbing service partner', type: 'Outsourced', specialization: 'Plumbing / Pump', contact: '+234 801 339 2275', source: 'Prime Water Works', availability: 'On Call' },
]

const filteredList = computed(() => {
  let list = technicians
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(t => t.name.toLowerCase().includes(q) || t.specialization.toLowerCase().includes(q) || t.contact.includes(q))
  }
  if (filterType.value) list = list.filter(t => t.type === filterType.value)
  if (filterSpec.value) list = list.filter(t => t.specialization === filterSpec.value)
  if (filterAvail.value) list = list.filter(t => t.availability === filterAvail.value)
  return list
})

function clearFilters() {
  search.value = ''
  filterType.value = ''
  filterSpec.value = ''
  filterAvail.value = ''
}

function availClass(a) {
  return {
    'Available': 'bg-green-100 text-green-600',
    'On Call': 'bg-yellow-100 text-yellow-600',
    'Unavailable': 'bg-red-500 text-white',
    'Booked': 'bg-gray-100 text-gray-600',
  }[a] || 'bg-gray-100 text-gray-500'
}

function viewTechnician(t) {
  router.push({ name: 'TechnicianView', params: { id: t.id } })
}
</script>