<template>
  <div class="space-y-4">

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">Edit Hall Booking</h2>
        <p class="text-xs text-gray-400 mt-0.5">Update draft hall booking before submission.</p>
      </div>
    </div>

    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 px-6 py-8 text-xs text-gray-400">
      Loading booking…
    </div>

    <div v-else style="display:grid;grid-template-columns:1fr 280px;gap:16px;align-items:start;">
      <div class="space-y-4">

        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-gray-900">Booking Details</h3>

            <button
              type="button"
              @click="showCustomerModal = true"
              class="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50"
            >
              + Add Customer
            </button>

            <button
              type="button"
              @click="openEditCustomerModal"
              class="px-4 py-2 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Edit Customer
            </button>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

            <div>
              <label class="text-xs text-gray-500 mb-1 block">
                Customer <span class="text-red-500">*</span>
              </label>

              <div class="relative">
                <input
                  v-model="customerSearch"
                  type="text"
                  placeholder="Search customer..."
                  :readonly="customerLocked"
                  @input="searchCustomers"
                  @focus="searchCustomers"
                  class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />

                <button
                  v-if="customerLocked"
                  type="button"
                  @click="clearSelectedCustomer"
                  class="absolute right-2 top-1/2 -translate-y-1/2 text-red-400 hover:text-red-600 text-xs"
                >
                  ✕
                </button>

                <div
                  v-if="showCustomerDropdown && customers.length && !customerLocked"
                  class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-56 overflow-y-auto"
                >
                  <button
                    v-for="c in customers"
                    :key="c.name"
                    type="button"
                    @click="selectCustomer(c)"
                    class="w-full text-left px-3 py-2 text-xs hover:bg-blue-50"
                  >
                    <div class="font-medium text-gray-800">
                      {{ c.customer_name || c.name }}
                    </div>

                    <div class="text-gray-400">
                      {{ c.name }}
                      <span v-if="c.mobile_no">• {{ c.mobile_no }}</span>
                    </div>
                  </button>
                </div>
              </div>
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Mobile Number</label>

              <div class="relative">
                <input
                  v-model="phoneSearch"
                  type="text"
                  placeholder="Search phone number..."
                  :readonly="phoneLocked"
                  @input="searchCustomersByPhone"
                  @focus="searchCustomersByPhone"
                  class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />

                <button
                  v-if="phoneLocked"
                  type="button"
                  @click="clearSelectedCustomer"
                  class="absolute right-2 top-1/2 -translate-y-1/2 text-red-400 hover:text-red-600 text-xs"
                >
                  ✕
                </button>

                <div
                  v-if="showPhoneDropdown && phoneResults.length && !phoneLocked"
                  class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-56 overflow-y-auto"
                >
                  <button
                    v-for="c in phoneResults"
                    :key="c.name"
                    type="button"
                    @click="selectCustomer(c)"
                    class="w-full text-left px-3 py-2 text-xs hover:bg-blue-50"
                  >
                    <div class="font-medium text-gray-800">
                      {{ c.mobile_no || 'No Phone Number' }}
                    </div>

                    <div class="text-gray-400">
                      {{ c.customer_name || c.name }}
                    </div>
                  </button>
                </div>
              </div>
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Hall <span class="text-red-500">*</span></label>
              <select
                v-model="form.hall"
                @change="onHallChange"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">— select hall —</option>
                <option v-for="h in halls" :key="h.name" :value="h.name">
                  {{ h.hall_name }} ({{ h.hall_type }})
                </option>
              </select>
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Event Type <span class="text-red-500">*</span></label>
              <select
                v-model="form.event_type"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">— select —</option>
                <option>Wedding</option>
                <option>Meeting</option>
                <option>Seminar</option>
                <option>Birthday</option>
                <option>Others</option>
              </select>
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Start Date <span class="text-red-500">*</span></label>
              <input
                v-model="form.start_datetime"
                 type="datetime-local"
                @change="computeTotals"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">End Date <span class="text-red-500">*</span></label>
              <input
                v-model="form.end_datetime"
                 type="datetime-local"
                @change="computeTotals"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Rate</label>
              <input
                v-model.number="form.rate"
                type="number"
                min="0"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Total Days</label>
              <input
                :value="form.total_days"
                type="text"
                readonly
                class="w-full text-xs border border-gray-100 rounded-lg px-3 py-2 bg-gray-50 text-gray-600 cursor-default"
              />
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Discount</h3>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <label class="text-xs text-gray-500 mb-1 block">Discount Type</label>
              <select
                v-model="form.discount_type"
                @change="computeTotals"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option>Percentage</option>
                <option>Fixed Amount</option>
              </select>
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">
                Discount {{ form.discount_type === 'Percentage' ? '(%)' : '(₦)' }}
              </label>
              <input
                v-model.number="form.discount_amount"
                type="number"
                min="0"
                @input="computeTotals"
                @change="computeTotals"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-sm font-bold text-gray-900">Additional Services</h3>
              <p class="text-xs text-gray-400 mt-0.5">Extra services billed alongside the hall.</p>
            </div>

            <div>
              <button
                @click="showServiceModal = true"
                class="px-3 py-1.5 text-xs font-medium text-green-600 border border-green-200 rounded-lg hover:bg-green-50"
              >
                + New Service
              </button>

              <button
                @click="addService"
                class="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50"
              >
                + Add Row
              </button>
            </div>
          </div>

          <div v-if="form.additional_billings.length === 0" class="text-center py-4 text-xs text-gray-400">
            No additional services added.
          </div>

          <table v-else class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left pb-2 text-xs font-semibold text-gray-500">Service</th>
                <th class="text-left pb-2 text-xs font-semibold text-gray-500">Qty</th>
                <th class="text-left pb-2 text-xs font-semibold text-gray-500">Rate</th>
                <th class="text-left pb-2 text-xs font-semibold text-gray-500">Discount Type</th>
                <th class="text-left pb-2 text-xs font-semibold text-gray-500">Discount</th>
                <th class="text-left pb-2 text-xs font-semibold text-gray-500">Amount</th>
                <th class="pb-2 w-6"></th>
              </tr>
            </thead>

            <tbody class="divide-y divide-gray-50">
              <tr v-for="(row, i) in form.additional_billings" :key="i">
                <td class="py-1.5 pr-2">
                  <select
                    v-model="row.service"
                    @change="onServiceChange(row)"
                    class="w-full text-xs border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="">— select —</option>
                    <option v-for="s in services" :key="s.name" :value="s.name">
                      {{ s.service }}
                    </option>
                  </select>
                </td>

                <td class="py-1.5 pr-2 w-16">
                  <input
                    v-model="row.qty"
                    type="number"
                    min="1"
                    @change="updateServiceRow(row)"
                    class="w-full text-xs border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </td>

                <td class="py-1.5 pr-2 w-24">
                  <input
                    v-model.number="row.rate"
                    type="number"
                    min="0"
                    @input="updateServiceRow(row)"
                    class="w-full text-xs border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </td>

                <td class="py-1.5 pr-2">
                  <select
                    v-model="row.discount_type"
                    @change="updateServiceRow(row)"
                    class="w-full text-xs border border-gray-200 rounded px-2 py-1.5"
                  >
                    <option value="Fixed Amount">Fixed Amount</option>
                    <option value="Percentage">Percentage</option>
                  </select>
                </td>
                <td class="py-1.5 pr-2 w-24">
                  <input
                    v-model.number="row.discount_amount"
                    type="number"
                    min="0"
                    @input="updateServiceRow(row)"
                    class="w-full text-xs border border-gray-200 rounded px-2 py-1.5"
                  />
                </td>

                <td class="py-1.5 pr-2 w-24">
                  <input
                    :value="row.amount"
                    type="text"
                    readonly
                    class="w-full text-xs border border-gray-100 rounded px-2 py-1.5 bg-gray-50 text-gray-600 cursor-default"
                  />
                </td>

                <td class="py-1.5">
                  <button @click="removeService(i)" class="text-red-400 hover:text-red-600 text-xs">
                    ✕
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="space-y-4">
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Booking Summary</h3>

          <div class="space-y-2 text-xs">
            <div class="flex justify-between">
              <span class="text-gray-500">Hall</span>
              <span class="font-medium text-gray-900">{{ form.hall || '–' }}</span>
            </div>

            <div class="flex justify-between">
              <span class="text-gray-500">Event</span>
              <span class="font-medium text-gray-900">{{ form.event_type || '–' }}</span>
            </div>

            <div class="flex justify-between">
              <span class="text-gray-500">Total Days</span>
              <span class="font-medium text-gray-900">{{ form.total_days || 0 }} day(s)</span>
            </div>

            <div class="flex justify-between">
              <span class="text-gray-500">Daily Rate</span>
              <span class="font-medium text-gray-900">₦{{ Number(form.rate || 0).toLocaleString() }}</span>
            </div>

            <div class="border-t border-gray-100 pt-2 flex justify-between">
              <span class="text-gray-500">Hall Total</span>
              <span class="font-medium text-gray-900">₦{{ Number(form.total_amount || 0).toLocaleString() }}</span>
            </div>

            <div class="flex justify-between">
              <span class="text-gray-500">Services</span>
              <span class="font-medium text-gray-900">₦{{ Number(servicesTotal).toLocaleString() }}</span>
            </div>

            <div v-if="form.discount_value > 0" class="flex justify-between text-red-500">
              <span>Discount Amount</span>
              <span>–₦{{ Number(form.discount_value || 0).toLocaleString() }}</span>
            </div>

            <div class="border-t border-gray-100 pt-2 flex justify-between font-bold">
              <span class="text-gray-700">Net Total</span>
              <span class="text-gray-900">₦{{ Number(form.net_total || 0).toLocaleString() }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 space-y-2">
          <button
            @click="saveChanges"
            :disabled="saving || !canSave"
            class="w-full px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ saving ? 'Saving…' : 'Save Changes' }}
          </button>

          <router-link :to="`/hall/booking/${route.params.id}`">
            <button class="w-full px-4 py-2 text-xs text-gray-500 hover:text-gray-700 transition-colors">
              Cancel
            </button>
          </router-link>

          <p v-if="error" class="text-xs text-red-500 mt-1">{{ error }}</p>
        </div>
      </div>
    </div>

    <div v-if="showServiceModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
  <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-5">
    <h3 class="text-sm font-bold text-gray-900 mb-4">
      Create Hotel Service
    </h3>

    <div class="space-y-3">
      <div>
        <label class="text-xs text-gray-500 mb-1 block">Service Name</label>
        <input
          v-model="serviceForm.service"
          type="text"
          placeholder="e.g. Chicken"
          class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2"
        />
      </div>

      <div>
        <label class="text-xs text-gray-500 mb-1 block">Rate</label>
        <input
          v-model.number="serviceForm.rate"
          type="number"
          min="0"
          placeholder="e.g. 2000"
          class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2"
        />
      </div>

      <p class="text-xs text-gray-400">
        This will create a non-stock Item under the Hall Service item group.
      </p>
    </div>

    <div class="flex justify-end gap-2 mt-5">
      <button
        type="button"
        @click="showServiceModal = false"
        class="px-4 py-2 text-xs border rounded-lg"
      >
        Cancel
      </button>

      <button
        type="button"
        @click="createHallService"
        class="px-4 py-2 text-xs text-white bg-blue-600 rounded-lg"
      >
        Create Service
      </button>
    </div>
  </div>
</div>

    <div v-if="showCustomerModal" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-lg w-full max-w-sm p-5">
        <h3 class="text-sm font-bold text-gray-900 mb-4">Add Customer</h3>

        <label class="text-xs text-gray-500 mb-1 block">Customer Name *</label>
        <input v-model="newCustomerName" class="w-full text-xs border rounded-lg px-3 py-2" />

        <label class="text-xs text-gray-500 mb-1 mt-3 block">Phone</label>
        <input v-model="newCustomerPhone" class="w-full text-xs border rounded-lg px-3 py-2" />

        <label class="text-xs text-gray-500 mb-1 mt-3 block">Email</label>
        <input v-model="newCustomerEmail" class="w-full text-xs border rounded-lg px-3 py-2" />

        <p v-if="customerError" class="text-xs text-red-500 mt-2">{{ customerError }}</p>
        <p v-if="customerSuccess" class="text-xs text-green-600 mt-2">{{ customerSuccess }}</p>

        <div class="flex justify-end gap-2 mt-5">
          <button @click="showCustomerModal = false" class="px-4 py-2 text-xs border rounded-lg">
            Cancel
          </button>

          <button @click="saveCustomer" :disabled="savingCustomer" class="px-4 py-2 text-xs text-white bg-blue-600 rounded-lg">
            {{ savingCustomer ? 'Saving…' : 'Save' }}
          </button>
        </div>
      </div>
    </div>

  </div>




  <!-- Edit Customer Modal -->
<div
  v-if="showEditCustomerModal"
  class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
>
  <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
    <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
      <h3 class="text-sm font-bold text-gray-900">Edit Customer Contact</h3>
      <button
        type="button"
        @click="closeEditCustomerModal"
        class="text-gray-400 hover:text-gray-600 text-lg leading-none"
      >
        ✕
      </button>
    </div>

    <div class="px-6 py-4 space-y-3">
      <!-- Search Customer -->
      <div class="relative">
        <label class="text-xs text-gray-500 mb-1 block">Search Customer</label>
        <input
          v-model="editCustomerSearch"
          type="text"
          placeholder="Search by name or phone..."
          @input="searchEditCustomers"
          @focus="searchEditCustomers"
          class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <div
          v-if="showEditCustomerDropdown && editCustomerResults.length"
          class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-56 overflow-y-auto"
        >
          <button
            v-for="c in editCustomerResults"
            :key="c.name"
            type="button"
            @click="selectEditCustomer(c)"
            class="w-full text-left px-3 py-2 text-xs hover:bg-blue-50"
          >
            <div class="font-medium text-gray-800">
              {{ c.customer_name || c.name }}
            </div>
            <div class="text-gray-400">
              {{ c.mobile_no || 'No phone' }} <span v-if="c.email_id">• {{ c.email_id }}</span>
            </div>
          </button>
        </div>
      </div>

      <!-- Selected Customer -->
      <div>
        <label class="text-xs text-gray-500 mb-1 block">Customer Name</label>
        <input
          v-model="editCustomerForm.customer_name"
          type="text"
          readonly
          class="w-full text-xs border border-gray-100 rounded-lg px-3 py-2 bg-gray-50 text-gray-500"
        />
      </div>

      <div>
        <label class="text-xs text-gray-500 mb-1 block">Phone</label>
        <input
          v-model="editCustomerForm.mobile_no"
          type="text"
          placeholder="Enter phone number"
          class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label class="text-xs text-gray-500 mb-1 block">Email</label>
        <input
          v-model="editCustomerForm.email_id"
          type="email"
          placeholder="Enter email address"
          class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <p v-if="editCustomerError" class="text-xs text-red-500">
        {{ editCustomerError }}
      </p>
    </div>

    <div class="px-6 py-4 border-t border-gray-100 flex gap-2">
      <button
        type="button"
        @click="closeEditCustomerModal"
        class="flex-1 px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
      >
        Cancel
      </button>

      <button
        type="button"
        @click="saveEditCustomer"
        :disabled="editCustomerSaving || !editCustomerForm.name"
        class="flex-1 px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {{ editCustomerSaving ? 'Saving…' : 'Save Changes' }}
      </button>
    </div>
  </div>
</div>


</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { callMethod } from '@/lib/api'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const saving = ref(false)
const error = ref(null)

const halls = ref([])
const services = ref([])
const customers = ref([])
const customerSearch = ref('')

const showCustomerModal = ref(false)
const newCustomerName = ref('')
const newCustomerPhone = ref('')
const newCustomerEmail = ref('')
const savingCustomer = ref(false)
const customerError = ref(null)
const customerSuccess = ref(null)

const phoneSearch = ref('')
const phoneResults = ref([])
const showPhoneDropdown = ref(false)
const customerLocked = ref(false)
const phoneLocked = ref(false)
const showCustomerDropdown = ref(false)

const showServiceModal = ref(false)

const serviceForm = ref({
  item_name: '',
  service: '',
  rate: 0,
})

const form = ref({
  customer_name: '',
  mobile_number: '',
  hall: '',
  event_type: '',
  start_datetime: '',
  end_datetime: '',
  rate: 0,
  total_days: 0,
  total_amount: 0,
  discount_value: 0,
  discount_type: 'Percentage',
  discount_amount: 0,
  net_total: 0,
  additional_billings: [],
})

const canSave = computed(() =>
  !!(form.value.customer_name && form.value.hall && form.value.event_type && form.value.start_datetime && form.value.end_datetime)
)

const servicesTotal = computed(() =>
  form.value.additional_billings.reduce((sum, r) => sum + (Number(r.amount) || 0), 0)
)

function toDateInput(value) {
  if (!value) return ''

  const d = new Date(value)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day}T${hour}:${minute}`
}

async function load() {
  loading.value = true
  error.value = null

  try {
    const [booking, h, s] = await Promise.all([
      callMethod('rhohotel.rhocom_hotel.api.hall_booking.get_booking', { name: route.params.id }),
      callMethod('rhohotel.rhocom_hotel.api.hall_booking.get_halls'),
      callMethod('rhohotel.rhocom_hotel.api.hall_booking.get_services'),
    ])

    if (booking.docstatus !== 0) {
      router.push(`/hall/booking/${booking.name}`)
      return
    }

    halls.value = h || []
    services.value = s || []
    customers.value = []
    

    form.value.customer_name = booking.customer_name || ''
    form.value.mobile_number = booking.mobile_number || ''
    form.value.hall = booking.hall || ''
    form.value.event_type = booking.event_type || ''
    form.value.start_datetime = toDateInput(booking.start_datetime)
    form.value.end_datetime = toDateInput(booking.end_datetime)
    form.value.rate = Number(booking.rate || 0)
    form.value.total_days = Number(booking.total_days || 0)
    form.value.total_amount = Number(booking.total_amount || 0)
    form.value.discount_value = 0
    form.value.discount_type = booking.discount_type || 'Percentage'
    form.value.discount_amount = Number(booking.discount_amount || 0)
    form.value.net_total = Number(booking.net_total || 0)

    form.value.additional_billings = (booking.additional_billings || []).map(r => ({
      service: r.service || '',
      qty: Number(r.qty || 1),
      rate: Number(r.rate || 0),
      discount_type: r.discount_type || 'Fixed Amount',
      discount_amount: Number(r.discount_amount || 0),
      amount: Number(r.amount || 0),
    }))

    const selected = customers.value.find(cus => cus.name === form.value.customer_name)
    customerSearch.value = selected ? (selected.customer_name || selected.name) : form.value.customer_name
    // Seed the customer dropdown with a search so existing selection appears
    if (form.value.customer_name) {
      const results = await callMethod(
        'rhohotel.rhocom_hotel.api.hall_booking.search_customers',
        { query: form.value.customer_name },
      ).catch(() => [])
      customers.value = results || []
    }
    phoneSearch.value = form.value.mobile_number || ''
    customerLocked.value = !!form.value.customer_name
    phoneLocked.value = !!form.value.mobile_number

    computeTotals()
  } catch (e) {
    error.value = e.message || 'Failed to load booking.'
  } finally {
    loading.value = false
  }
}

async function onHallChange() {
  if (!form.value.hall) {
    form.value.rate = 0
    computeTotals()
    return
  }

  const rate = await callMethod(
    'rhohotel.rhocom_hotel.api.hall_booking.get_hall_rate',
    {
      hall_name: form.value.hall
    }
  )

  form.value.rate = Number(rate) || 0

  computeTotals()
}

async function searchCustomers() {
  if (customerLocked.value) return

  const data = await callMethod(
    'rhohotel.rhocom_hotel.api.hall_booking.search_customers',
    { query: customerSearch.value }
  )

  customers.value = data || []
  showCustomerDropdown.value = true
}

async function searchCustomersByPhone() {
  if (phoneLocked.value) return

  const data = await callMethod(
    'rhohotel.rhocom_hotel.api.hall_booking.search_customers',
    { query: phoneSearch.value }
  )

  phoneResults.value = data || []
  showPhoneDropdown.value = true
}

function selectCustomer(c) {
  form.value.customer_name = c.name
  form.value.mobile_number = c.mobile_no || ''

  customerSearch.value = c.customer_name || c.name
  phoneSearch.value = c.mobile_no || ''

  customerLocked.value = true
  phoneLocked.value = true

  showCustomerDropdown.value = false
  showPhoneDropdown.value = false
}

function clearSelectedCustomer() {
  form.value.customer_name = ''
  form.value.mobile_number = ''

  customerSearch.value = ''
  phoneSearch.value = ''

  customerLocked.value = false
  phoneLocked.value = false

  showCustomerDropdown.value = false
  showPhoneDropdown.value = false
}


function computeTotals() {
  const start = new Date(form.value.start_datetime)
  const end = new Date(form.value.end_datetime)

  if (!form.value.start_datetime || !form.value.end_datetime || end <= start) {
    form.value.total_days = 0
    form.value.total_amount = 0
    form.value.discount_value = 0
    form.value.net_total = 0
    return
  }

  const startDate = new Date(
  start.getFullYear(),
  start.getMonth(),
  start.getDate()
)

const endDate = new Date(
  end.getFullYear(),
  end.getMonth(),
  end.getDate()
)

const days =
  Math.floor((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1

  const hallTotal = Number(form.value.rate || 0) * days
  const svcTotal = servicesTotal.value

  let discountValue = Number(
    form.value.discount_amount || 0
  )

  let hallDiscount = 0

  if (form.value.discount_type === 'Percentage') {

    if (discountValue > 100) {
      discountValue = 100
      form.value.discount_amount = 100
    }

    hallDiscount = hallTotal * (discountValue / 100)

  } else {

    if (discountValue > hallTotal) {
      discountValue = hallTotal
      form.value.discount_amount = hallTotal
    }

    hallDiscount = discountValue
  }

  form.value.total_days = days
  form.value.total_amount = hallTotal
  form.value.discount_value = hallDiscount

  form.value.net_total =
    (hallTotal - hallDiscount) + svcTotal
}

function addService() {
  form.value.additional_billings.push({
    service: '',
    qty: 1,
    rate: 0,
    discount_type: 'Fixed Amount',
    discount_amount: 0,
    amount: 0,
  })
}

function removeService(index) {
  form.value.additional_billings.splice(index, 1)
  computeTotals()
}

function onServiceChange(row) {
  const found = services.value.find(s => s.name === row.service)
  if (found) row.rate = Number(found.rate) || 0
  updateServiceRow(row)
}

function updateServiceRow(row) {
  const qty = Number(row.qty || 0)
  const rate = Number(row.rate || 0)

  const gross = qty * rate

  let discountValue = Number(
    row.discount_amount || 0
  )

  let discount = 0

  if (row.discount_type === 'Percentage') {

    if (discountValue > 100) {
      discountValue = 100
      row.discount_amount = 100
    }

    discount = gross * (discountValue / 100)

  } else {

    if (discountValue > gross) {
      discountValue = gross
      row.discount_amount = gross
    }

    discount = discountValue
  }

  row.amount = gross - discount

  computeTotals()
}

async function saveCustomer() {
  customerSuccess.value = null
  customerError.value = null

  if (!newCustomerName.value.trim()) {
    customerError.value = 'Customer name is required.'
    return
  }

  savingCustomer.value = true

  try {
    const result = await callMethod('rhohotel.rhocom_hotel.api.hall_booking.create_customer', {
      customer_name: newCustomerName.value.trim(),
      mobile_no: newCustomerPhone.value.trim(),
      email_id: newCustomerEmail.value.trim(),
    })

    form.value.customer_name = result.name
    form.value.mobile_number = result.mobile_no || ''

    customerSearch.value = result.customer_name || result.name
    phoneSearch.value = result.mobile_no || ''

    customerLocked.value = true
    phoneLocked.value = true

    customerSuccess.value = 'Customer added successfully.'

    setTimeout(() => {
      showCustomerModal.value = false
      newCustomerName.value = ''
      newCustomerPhone.value = ''
      newCustomerEmail.value = ''
      customerSuccess.value = null
    }, 800)
  } catch (e) {
    customerError.value = e.message || 'Failed to create customer.'
  } finally {
    savingCustomer.value = false
  }
}


async function createHallService() {
  if (!serviceForm.value.service) return

  const created = await callMethod(
    'rhohotel.rhocom_hotel.api.hall_booking.create_hall_service',
    {
      data: JSON.stringify({
        service: serviceForm.value.service,
        rate: serviceForm.value.rate,
      })
    }
  )

  services.value.push(created)
  showServiceModal.value = false

  serviceForm.value = {
    item_name: '',
    service: '',
    rate: 0,
  }
}


function normalizePhone(phone) {
  if (!phone) return ''

  phone = phone.trim()

  if (phone.startsWith('0')) {
    return '+234' + phone.substring(1)
  }

  if (phone.startsWith('234')) {
    return '+' + phone
  }

  return phone
}

async function saveChanges() {
  if (!canSave.value) return

  saving.value = true
  error.value = null

  try {
    const payload = {
      ...form.value,
      mobile_number: normalizePhone(form.value.mobile_number),
    }

    await callMethod('rhohotel.rhocom_hotel.api.hall_booking.update_booking', {
      name: route.params.id,
      data: JSON.stringify(payload)
    })

    router.push(`/hall/booking/${route.params.id}`)
  } catch (e) {
    error.value = e.message || 'Failed to update booking.'
  } finally {
    saving.value = false
  }
}




const showEditCustomerModal = ref(false)
const editCustomerSearch = ref('')
const editCustomerResults = ref([])
const showEditCustomerDropdown = ref(false)
const editCustomerSaving = ref(false)
const editCustomerError = ref(null)

const editCustomerForm = ref({
  name: '',
  customer_name: '',
  mobile_no: '',
  email_id: '',
})

function openEditCustomerModal() {
  editCustomerError.value = null
  showEditCustomerModal.value = true
}

function closeEditCustomerModal() {
  showEditCustomerModal.value = false
  editCustomerSearch.value = ''
  editCustomerResults.value = []
  showEditCustomerDropdown.value = false
  editCustomerError.value = null
  editCustomerForm.value = {
    name: '',
    customer_name: '',
    mobile_no: '',
    email_id: '',
  }
}

let editCustomerSearchTimer = null

function searchEditCustomers() {
  clearTimeout(editCustomerSearchTimer)

  editCustomerSearchTimer = setTimeout(async () => {
    try {
      const res = await callMethod(
        'rhohotel.rhocom_hotel.api.hall_booking.search_customers',
        { query: editCustomerSearch.value || '' }
      )

      editCustomerResults.value = res || []
      showEditCustomerDropdown.value = true
    } catch (e) {
      console.error(e)
    }
  }, 250)
}

function selectEditCustomer(c) {
  editCustomerForm.value = {
    name: c.name,
    customer_name: c.customer_name || c.name,
    mobile_no: c.mobile_no || '',
    email_id: c.email_id || '',
  }

  editCustomerSearch.value = c.customer_name || c.name
  showEditCustomerDropdown.value = false
}

async function saveEditCustomer() {
  if (!editCustomerForm.value.name) {
    editCustomerError.value = 'Please select a customer first.'
    return
  }

  editCustomerSaving.value = true
  editCustomerError.value = null

  try {
    const updated = await callMethod(
      'rhohotel.rhocom_hotel.api.hall_booking.update_customer_contact',
      {
        customer: editCustomerForm.value.name,
        mobile_no: editCustomerForm.value.mobile_no,
        email_id: editCustomerForm.value.email_id,
      }
    )

    // Update customers list
    customers.value = customers.value.map(c =>
      c.name === updated.name ? { ...c, ...updated } : c
    )

    // Update phone search list
    phoneResults.value = phoneResults.value.map(c =>
      c.name === updated.name ? { ...c, ...updated } : c
    )

    // Update current selected customer immediately
    if (form.value.customer_name === updated.name) {
      form.value.mobile_number = updated.mobile_no || ''
      phoneSearch.value = updated.mobile_no || ''
      customerSearch.value = updated.customer_name || updated.name
      customerLocked.value = true
      phoneLocked.value = !!updated.mobile_no
    }

    closeEditCustomerModal()
  } catch (e) {
    editCustomerError.value = e.message || 'Failed to update customer.'
  } finally {
    editCustomerSaving.value = false
  }
}



onMounted(load)
</script>