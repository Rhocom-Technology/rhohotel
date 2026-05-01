<template>
  <div style="background:#f1f5f9;min-height:100%;" class="p-6 space-y-4">

    <!-- Toast -->
    <transition-group name="toast" tag="div" class="fixed top-4 right-4 z-50 space-y-2" style="min-width:280px;max-width:360px;">
      <div v-for="t in toasts" :key="t.id"
        class="flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg text-sm font-medium border"
        :class="{
          'bg-white border-green-200 text-green-800': t.type === 'success',
          'bg-white border-red-200 text-red-800':   t.type === 'error',
          'bg-white border-yellow-200 text-yellow-800': t.type === 'warning',
        }">
        <span class="text-base leading-none mt-0.5">{{ t.type === 'success' ? '✅' : t.type === 'error' ? '❌' : '⚠️' }}</span>
        <span class="flex-1 leading-snug">{{ t.message }}</span>
        <button @click="removeToast(t.id)" class="opacity-50 hover:opacity-100 text-xs">✕</button>
      </div>
    </transition-group>

    <!-- Header -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">New Technician</h2>
        <p class="text-xs text-gray-400 mt-0.5">Capture identity, source type, specialization, contact details, and linkage.</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="router.push('/maintenance/technicians')" class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
          Cancel
        </button>
        <button @click="saveTechnician" :disabled="saving"
          class="px-4 py-2 text-xs font-semibold text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center gap-1.5">
          <svg v-if="saving" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          {{ saving ? 'Saving...' : 'Save Technician' }}
        </button>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 300px;gap:20px;">

      <!-- Left Column -->
      <div class="space-y-4">

        <!-- Type & Availability -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Technician Details</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Technician ID</p>
              <div class="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-400 italic">
                Auto-generated on save
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Technician Type <span class="text-red-400">*</span></p>
              <div class="flex rounded-lg overflow-hidden border border-gray-200">
                <button
                  @click="form.technician_type = 'In-House'"
                  class="flex-1 py-2.5 text-xs font-medium transition-colors"
                  :class="form.technician_type === 'In-House'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'">
                  🏢 In-House
                </button>
                <button
                  @click="form.technician_type = 'Outsourced'"
                  class="flex-1 py-2.5 text-xs font-medium transition-colors border-l border-gray-200"
                  :class="form.technician_type === 'Outsourced'
                    ? 'bg-orange-500 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'">
                  🔧 Outsourced
                </button>
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Availability</p>
              <select v-model="form.availability" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                <option value="Available">Available</option>
                <option value="On Call">On Call</option>
                <option value="Unavailable">Unavailable</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Identity & Source -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-1">Identity & Source</h3>

          <!-- In-House context note -->
          <p v-if="form.technician_type === 'In-House'" class="text-xs text-blue-600 bg-blue-50 rounded-lg px-3 py-2 mb-4">
            In-house technicians belong to your company. Link them to an existing employee record — their contact details will be pre-filled automatically.
          </p>
          <p v-else class="text-xs text-orange-600 bg-orange-50 rounded-lg px-3 py-2 mb-4">
            Outsourced technicians are external contractors or vendors. Link them to a supplier record, or fill in details manually.
          </p>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">
                {{ form.technician_type === 'In-House' ? 'Full Name' : 'Full Name / Company Name' }}
                <span class="text-red-400">*</span>
              </p>
              <input v-model="form.technician_name" type="text"
                :placeholder="form.technician_type === 'In-House' ? 'Auto-filled from employee, or enter manually' : 'Enter full name or company name'"
                class="w-full px-3 py-2.5 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
                :class="attempted && !form.technician_name.trim() ? 'border-red-300 bg-red-50' : 'border-gray-200'" />
              <p v-if="attempted && !form.technician_name.trim()" class="text-[10px] text-red-500 mt-1">Required</p>
            </div>

            <!-- In-House: Employee link -->
            <div v-if="form.technician_type === 'In-House'">
              <p class="text-xs text-gray-500 mb-1.5">Link Employee</p>
              <select v-model="form.employee" @change="onEmployeeSelect"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                <option value="">— select employee —</option>
                <option v-for="emp in employees" :key="emp.name" :value="emp.name">
                  {{ emp.employee_name }}{{ emp.designation ? ` · ${emp.designation}` : '' }}
                </option>
              </select>
            </div>

            <!-- Outsourced: Vendor/Supplier link -->
            <div v-else>
              <p class="text-xs text-gray-500 mb-1.5">Link Supplier / Vendor</p>
              <select v-model="form.supplier" @change="onSupplierSelect"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                <option value="">— select supplier —</option>
                <option v-for="sup in suppliers" :key="sup.name" :value="sup.name">
                  {{ sup.supplier_name }}{{ sup.supplier_type ? ` · ${sup.supplier_type}` : '' }}
                </option>
              </select>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Primary Specialization</p>
              <select v-model="form.primary_specialization"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-600">
                <option value="">Select specialization</option>
                <option value="Laundry / Mechanical">Laundry / Mechanical</option>
                <option value="Boiler / Heating">Boiler / Heating</option>
                <option value="Electrical / Electronics">Electrical / Electronics</option>
                <option value="HVAC">HVAC</option>
                <option value="Plumbing / Pump">Plumbing / Pump</option>
                <option value="TV / Smart Lock / IT">TV / Smart Lock / IT</option>
                <option value="General Maintenance">General Maintenance</option>
              </select>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Secondary Skills</p>
              <input v-model="form.secondary_skills" type="text"
                placeholder="e.g. Electrical, HVAC, Plumbing..."
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;" class="mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Phone</p>
              <input v-model="form.phone" type="text" placeholder="Enter phone number"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Email</p>
              <input v-model="form.email" type="email" placeholder="Enter email address"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Shift / Working Window</p>
              <input v-model="form.shift" type="text" placeholder="e.g. 08:00 AM – 05:00 PM"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1.5">Response Priority Group</p>
              <select v-model="form.response_priority_group"
                class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700">
                <option value="Standard">Standard</option>
                <option value="Priority">Priority</option>
                <option value="Emergency">Emergency</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Notes & Extras -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Notes & Categories</h3>
          <div class="mb-4">
            <p class="text-xs text-gray-500 mb-1.5">Notes</p>
            <textarea v-model="form.notes" rows="3"
              placeholder="Service scope, experience note, preferred sites, safety instruction, or escalation note..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
          </div>
          <div class="mb-4">
            <p class="text-xs text-gray-500 mb-1.5">Supported Asset Categories</p>
            <textarea v-model="form.supported_categories" rows="2"
              placeholder="Laundry equipment, HVAC, pumps, room electronics, power systems..."
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"></textarea>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1.5">Certification / License</p>
            <input v-model="form.certification" type="text"
              placeholder="License number, vendor approval, or professional certification"
              class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300" />
          </div>
        </div>

      </div>

      <!-- Right Column -->
      <div class="space-y-4">

        <!-- Quick Toggles -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Permissions & Flags</h3>
          <div class="space-y-3">
            <label class="flex items-start gap-3 cursor-pointer group">
              <div class="mt-0.5">
                <input type="checkbox" v-model="form.can_receive_urgent"
                  class="w-4 h-4 accent-green-500" />
              </div>
              <div>
                <p class="text-xs font-medium text-gray-700 group-hover:text-gray-900">Can receive urgent tasks</p>
                <p class="text-[10px] text-gray-400 mt-0.5">Will be included in urgent / emergency dispatch pool</p>
              </div>
            </label>
            <label class="flex items-start gap-3 cursor-pointer group">
              <div class="mt-0.5">
                <input type="checkbox" v-model="form.visible_for_assignment"
                  class="w-4 h-4 accent-green-500" />
              </div>
              <div>
                <p class="text-xs font-medium text-gray-700 group-hover:text-gray-900">Visible for task assignment</p>
                <p class="text-[10px] text-gray-400 mt-0.5">Appears in the assignee dropdown on maintenance tasks</p>
              </div>
            </label>
          </div>
        </div>

        <!-- Live Preview -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Preview</h3>

          <!-- Type badge -->
          <div class="flex items-center gap-2 mb-3">
            <span class="px-2.5 py-1 rounded-full text-xs font-semibold"
              :class="form.technician_type === 'In-House'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-orange-100 text-orange-700'">
              {{ form.technician_type === 'In-House' ? '🏢 In-House' : '🔧 Outsourced' }}
            </span>
            <span class="px-2.5 py-1 rounded-full text-xs font-semibold"
              :class="{
                'bg-green-100 text-green-700': form.availability === 'Available',
                'bg-yellow-100 text-yellow-700': form.availability === 'On Call',
                'bg-gray-100 text-gray-500': form.availability === 'Unavailable',
              }">
              {{ form.availability }}
            </span>
          </div>

          <div class="space-y-1.5">
            <div class="flex justify-between">
              <span class="text-xs text-gray-400">Name</span>
              <span class="text-xs font-medium text-gray-800 text-right max-w-[160px] truncate">
                {{ form.technician_name || '—' }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-400">{{ form.technician_type === 'In-House' ? 'Employee' : 'Supplier' }}</span>
              <span class="text-xs font-medium text-gray-800">
                {{ linkedLabel || '—' }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-400">Specialization</span>
              <span class="text-xs font-medium text-gray-800">{{ form.primary_specialization || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-400">Phone</span>
              <span class="text-xs font-medium text-gray-800">{{ form.phone || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-400">Priority Group</span>
              <span class="text-xs font-semibold px-2 py-0.5 rounded-full"
                :class="{
                  'bg-red-100 text-red-600':    form.response_priority_group === 'Emergency',
                  'bg-blue-100 text-blue-600':  form.response_priority_group === 'Priority',
                  'bg-gray-100 text-gray-600':  form.response_priority_group === 'Standard',
                }">{{ form.response_priority_group }}</span>
            </div>
            <div class="flex justify-between pt-1 border-t border-gray-100 mt-1">
              <span class="text-xs text-gray-400">Urgent tasks</span>
              <span class="text-xs font-medium" :class="form.can_receive_urgent ? 'text-green-600' : 'text-gray-400'">
                {{ form.can_receive_urgent ? 'Yes' : 'No' }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-400">Assignable</span>
              <span class="text-xs font-medium" :class="form.visible_for_assignment ? 'text-green-600' : 'text-gray-400'">
                {{ form.visible_for_assignment ? 'Yes' : 'No' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Validation summary when attempted with errors -->
        <div v-if="attempted && validationErrors.length" class="bg-red-50 rounded-xl border border-red-200 p-4">
          <p class="text-xs font-semibold text-red-700 mb-2">Please fix the following:</p>
          <ul class="space-y-1">
            <li v-for="e in validationErrors" :key="e" class="text-xs text-red-600 flex items-start gap-1.5">
              <span class="shrink-0">•</span>{{ e }}
            </li>
          </ul>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const router = useRouter()
const saving = ref(false)
const attempted = ref(false)

// ─── Toast ────────────────────────────────────────────────────────────────────
const toasts = ref([])
let toastId = 0
function showToast(message, type = 'error', duration = 4500) {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, duration)
}
function removeToast(id) { toasts.value = toasts.value.filter(t => t.id !== id) }

// ─── Form ─────────────────────────────────────────────────────────────────────
const form = ref({
  technician_type: 'In-House',
  technician_name: '',
  availability: 'Available',
  employee: '',
  supplier: '',
  primary_specialization: '',
  secondary_skills: '',
  phone: '',
  email: '',
  shift: '',
  response_priority_group: 'Standard',
  can_receive_urgent: true,
  visible_for_assignment: true,
  notes: '',
  supported_categories: '',
  certification: '',
})

// Clear linkage when type switches
watch(() => form.value.technician_type, () => {
  form.value.employee = ''
  form.value.supplier = ''
  // Don't clear name/phone/email — user may have typed manually
})

// ─── Data ─────────────────────────────────────────────────────────────────────
const employeesResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.technician.get_employees_for_technician',
  auto: true
})
const employees = computed(() => employeesResource.data || [])

const suppliersResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.technician.get_vendors_for_technician',
  auto: true
})
const suppliers = computed(() => suppliersResource.data || [])

// ─── Auto-fill from employee ──────────────────────────────────────────────────
function onEmployeeSelect() {
  if (!form.value.employee) return
  const emp = employees.value.find(e => e.name === form.value.employee)
  if (!emp) return
  if (!form.value.technician_name) form.value.technician_name = emp.employee_name
  if (!form.value.phone && emp.cell_number) form.value.phone = emp.cell_number
  if (!form.value.email && emp.personal_email) form.value.email = emp.personal_email
}

// ─── Auto-fill from supplier ──────────────────────────────────────────────────
function onSupplierSelect() {
  if (!form.value.supplier) return
  const sup = suppliers.value.find(s => s.name === form.value.supplier)
  if (!sup) return
  if (!form.value.technician_name) form.value.technician_name = sup.supplier_name
  if (!form.value.phone && sup.mobile_no) form.value.phone = sup.mobile_no
  if (!form.value.email && sup.email_id) form.value.email = sup.email_id
}

// ─── Preview label ────────────────────────────────────────────────────────────
const linkedLabel = computed(() => {
  if (form.value.technician_type === 'In-House' && form.value.employee) {
    const emp = employees.value.find(e => e.name === form.value.employee)
    return emp?.employee_name || form.value.employee
  }
  if (form.value.technician_type === 'Outsourced' && form.value.supplier) {
    const sup = suppliers.value.find(s => s.name === form.value.supplier)
    return sup?.supplier_name || form.value.supplier
  }
  return null
})

// ─── Validation ───────────────────────────────────────────────────────────────
const validationErrors = computed(() => {
  if (!attempted.value) return []
  const errors = []
  if (!form.value.technician_name.trim()) errors.push('Technician name is required')
  if (!form.value.technician_type) errors.push('Technician type is required')
  return errors
})

// ─── Save ─────────────────────────────────────────────────────────────────────
const createResource_ = createResource({
  url: 'rhohotel.rhocom_hotel.api.technician.create_technician',
  auto: false
})

async function saveTechnician() {
  attempted.value = true
  if (validationErrors.value.length) {
    validationErrors.value.forEach(e => showToast(e))
    return
  }

  saving.value = true
  try {
    const response = await createResource_.fetch({
      technician_data: form.value
    })
    console.log('[NewTechnician] createTechnician response:', response)
    if (response?.success && response?.technician_name) {
      showToast('Technician created successfully', 'success')
      setTimeout(() => router.replace(`/maintenance/technicians/${response.technician_name}`), 600)
    } else {
      const errMsg = response?.error || JSON.stringify(response)
      console.error('[NewTechnician] failed:', errMsg)
      showToast('Failed to create technician: ' + errMsg)
    }
  } catch (e) {
    console.error('[NewTechnician] exception:', e)
    showToast('Error: ' + (e?.message || String(e)))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>