<template>
  <div class="space-y-4">

    <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-gray-900">New Hall Booking</h2>
        <p class="text-xs text-gray-400 mt-0.5">Create a new hall booking. Submit to confirm and generate invoice.</p>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 280px;gap:16px;align-items:start;">

      <!-- Left -->
      <div class="space-y-4">

        <!-- Booking Details -->
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
                      <span v-if="c.mobile_no">
                        • {{ c.mobile_no }}
                      </span>
                    </div>
                  </button>
                </div>
              </div>
            </div>

            <div>
  <label class="text-xs text-gray-500 mb-1 block">
    Mobile Number
  </label>

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
              <select v-model="form.hall" @change="onHallChange"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">— select hall —</option>
                <option v-for="h in halls" :key="h.name" :value="h.name">{{ h.hall_name }} ({{ h.hall_type }})</option>
              </select>
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Event Type <span class="text-red-500">*</span></label>
              <select v-model="form.event_type"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">— select —</option>
                <option>Wedding</option>
                <option>Meeting</option>
                <option>Seminar</option>
                <option>Birthday</option>
                <option>Others</option>
              </select>
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Start Date &amp; Time <span class="text-red-500">*</span></label>
              <input v-model="form.start_datetime" type="datetime-local" @change="computeTotals"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">End Date &amp; Time <span class="text-red-500">*</span></label>
              <input v-model="form.end_datetime" type="datetime-local" @change="computeTotals"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Rate Per Hour</label>
              <input v-model="form.rate" type="number" @change="computeTotals"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <label class="text-xs text-gray-500 mb-1 block">Total Hours</label>
              <input :value="form.total_hours" type="text" readonly
                class="w-full text-xs border border-gray-100 rounded-lg px-3 py-2 bg-gray-50 text-gray-600 cursor-default" />
            </div>

          </div>
        </div>

        <!-- Discount -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h3 class="text-sm font-bold text-gray-900 mb-4">Discount</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <label class="text-xs text-gray-500 mb-1 block">Discount Type</label>
             <select
                v-model="form.discount_type"
                @change="computeTotals"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
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

        <!-- Additional Services -->
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
                <th class="text-left pb-2 text-xs font-semibold text-gray-500">Amount</th>
                
                <th class="pb-2 w-6"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="(row, i) in form.additional_billings" :key="i">
                <td class="py-1.5 pr-2">
                  <select v-model="row.service" @change="onServiceChange(row)"
                    class="w-full text-xs border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500">
                    <option value="">— select —</option>
                    <option v-for="s in services" :key="s.name" :value="s.name">{{ s.service }}</option>
                  </select>
                </td>
                <td class="py-1.5 pr-2 w-16">
                  <input v-model="row.qty" type="number" min="1" @change="updateServiceRow(row)"
                    class="w-full text-xs border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500" />
                </td>
                <td class="py-1.5 pr-2 w-24">
                  <input v-model="row.rate" type="number" min="0" @change="updateServiceRow(row)"
                    class="w-full text-xs border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500" />
                </td>
                <td class="py-1.5 pr-2 w-24">
                  <input :value="row.amount" type="text" readonly
                    class="w-full text-xs border border-gray-100 rounded px-2 py-1.5 bg-gray-50 text-gray-600 cursor-default" />
                </td>
                <td class="py-1.5">
                  <button @click="form.additional_billings.splice(i,1)" class="text-red-400 hover:text-red-600 text-xs">✕</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>

      <!-- Right: Summary + Actions -->
      <div class="space-y-4">

        <!-- Booking Summary -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3">Booking Summary</h3>
          <div class="space-y-2 text-xs">
           
            <div class="flex justify-between"><span class="text-gray-500">Hall</span><span class="font-medium text-gray-900">{{ form.hall || '–' }}</span></div>
            <div class="flex justify-between"><span class="text-gray-500">Event</span><span class="font-medium text-gray-900">{{ form.event_type || '–' }}</span></div>
            <div class="flex justify-between"><span class="text-gray-500">Total Hours</span><span class="font-medium text-gray-900">{{ form.total_hours || 0 }}h</span></div>
            <div class="flex justify-between"><span class="text-gray-500">Rate/hr</span><span class="font-medium text-gray-900">₦{{ Number(form.rate || 0).toLocaleString() }}</span></div>
            <div class="border-t border-gray-100 pt-2 flex justify-between"><span class="text-gray-500">Hall Total</span><span class="font-medium text-gray-900">₦{{ Number(form.total_amount || 0).toLocaleString() }}</span></div>
            <div class="flex justify-between"><span class="text-gray-500">Services</span><span class="font-medium text-gray-900">₦{{ Number(servicesTotal).toLocaleString() }}</span></div>
             <div v-if="form.discount_value > 0" class="flex justify-between text-red-500">
                <span>Discount Amount</span>
                <span>–₦{{ Number(form.discount_value || 0).toLocaleString() }}</span>
            </div>
            <div v-if="form.discount_amount > 0" class="flex justify-between text-red-500">
              <span>Discount</span>
              <span>–{{ form.discount_type === 'Percentage' ? form.discount_amount + '%' : '₦' + Number(form.discount_amount).toLocaleString() }}</span>
            </div>
            <div class="border-t border-gray-100 pt-2 flex justify-between font-bold">
              <span class="text-gray-700">Net Total</span>
              <span class="text-gray-900">₦{{ Number(form.net_total || 0).toLocaleString() }}</span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="bg-white rounded-xl border border-gray-200 px-5 py-4 space-y-2">
          <button @click="save(false)" :disabled="saving || !canSave"
            class="w-full px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {{ saving ? 'Saving…' : 'Save as Draft' }}
          </button>
          <button @click="save(true)" :disabled="saving || !canSave"
            class="w-full px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {{ saving ? 'Saving…' : 'Submit & Create Invoice' }}
          </button>
          <router-link to="/hall/booking">
            <button class="w-full px-4 py-2 text-xs text-gray-500 hover:text-gray-700 transition-colors">Cancel</button>
          </router-link>
          <p v-if="error" class="text-xs text-red-500 mt-1">{{ error }}</p>
        </div>

      </div>
    </div>



    <div v-if="showServiceModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
        <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-5">
            <h3 class="text-sm font-bold text-gray-900 mb-4">
            Create Additional Service
            </h3>

            <div class="space-y-3">
           <div class="relative">
  <label class="text-xs text-gray-500 mb-1 block">Item</label>

  <input
    v-model="itemSearch"
    type="text"
    placeholder="Search ERPNext item..."
    @input="searchItems"
    @focus="searchItems"
    class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2"
  />

  <div
    v-if="showItemDropdown && itemResults.length"
    class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-56 overflow-y-auto"
  >
    <button
      v-for="i in itemResults"
      :key="i.item_code"
      type="button"
      @click="selectServiceItem(i)"
      class="w-full text-left px-3 py-2 text-xs hover:bg-blue-50"
    >
      <div class="font-medium text-gray-800">
        {{ i.item_name || i.item_code }}
      </div>
      <div class="text-gray-400">
        {{ i.item_code }}
      </div>
    </button>
  </div>
</div>

            <div>
                <label class="text-xs text-gray-500 mb-1 block">Service</label>
                <input
                v-model="serviceForm.service"
                type="text"
                readonly
                class="w-full text-xs border border-gray-100 rounded-lg px-3 py-2 bg-gray-50 text-gray-500"
                />
            </div>

            <div>
                <label class="text-xs text-gray-500 mb-1 block">Rate</label>
                <input
                v-model="serviceForm.rate"
                type="number"
                min="0"
                class="w-full text-xs border border-gray-200 rounded-lg px-3 py-2"
                />
            </div>
            </div>

            <div class="flex justify-end gap-2 mt-5">
            <button
                @click="showServiceModal = false"
                class="px-4 py-2 text-xs border rounded-lg"
            >
                Cancel
            </button>

            <button
                @click="createHallService"
                class="px-4 py-2 text-xs text-white bg-blue-600 rounded-lg"
            >
                Create Service
            </button>
            </div>
        </div>
    </div>

  </div>


  <div
  v-if="showCustomerModal"
  class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50"
>
  <div class="bg-white rounded-xl shadow-lg w-full max-w-sm p-5">
    <h3 class="text-sm font-bold text-gray-900 mb-4">Add Customer</h3>

    <label class="text-xs text-gray-500 mb-1 block">Customer Name *</label>
    <input v-model="newCustomerName" class="w-full text-xs border rounded-lg px-3 py-2" />

    <label class="text-xs text-gray-500 mb-1 mt-3 block">Phone</label>
    <input v-model="newCustomerPhone" class="w-full text-xs border rounded-lg px-3 py-2" />

    <label class="text-xs text-gray-500 mb-1 mt-3 block">Email</label>
    <input v-model="newCustomerEmail" class="w-full text-xs border rounded-lg px-3 py-2" />

    <p v-if="customerError" class="text-xs text-red-500 mt-2">{{ customerError }}</p>
    <p v-if="customerSuccess" class="text-xs text-green-600 mt-2">
      {{ customerSuccess }}
    </p>

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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { callMethod } from '@/lib/api'


const router = useRouter()
const route = useRoute()

const saving  = ref(false)
const error   = ref(null)
const halls    = ref([])
const services = ref([])
const customers = ref([])
const customerSearch = ref('')

const allItems = ref([])
const itemSearch = ref('')
const itemResults = ref([])
const showItemDropdown = ref(false)

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
  customer_name:       '',
  mobile_number:       '',
  hall:                '',
  event_type:          '',
  start_datetime:      '',
  end_datetime:        '',
  rate:                0,
  total_hours:         0,
  total_amount:        0,
   discount_value: 0,
  discount_type:       'Percentage',
  discount_amount:     0,
  net_total:           0,
  additional_billings: [],
})

const canSave = computed(() =>
  !!(form.value.customer_name && form.value.hall && form.value.event_type &&
     form.value.start_datetime && form.value.end_datetime)
)

const servicesTotal = computed(() =>
  form.value.additional_billings.reduce((sum, r) => sum + (Number(r.amount) || 0), 0)
)

async function onHallChange() {
  if (!form.value.hall) { form.value.rate = 0; return }
  const rate = await callMethod('rhohotel.rhocom_hotel.api.hall_booking.get_hall_rate', { hall_name: form.value.hall })
  form.value.rate = Number(rate) || 0
  computeTotals()
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


function computeTotals() {
  const start = new Date(form.value.start_datetime)
  const end = new Date(form.value.end_datetime)

  if (!form.value.start_datetime || !form.value.end_datetime || end <= start) {
    form.value.total_hours = 0
    form.value.total_amount = 0
    form.value.discount_value = 0
    form.value.net_total = 0
    return
  }

  const hours = Math.ceil((end - start) / 3600000)
  const hallTotal = Number(form.value.rate || 0) * hours
  const svcTotal = servicesTotal.value
  const grossTotal = hallTotal + svcTotal

  const discountAmount = Number(form.value.discount_amount || 0)
  let discount = 0

  if (discountAmount > 0) {
    if (form.value.discount_type === 'Percentage') {
      discount = grossTotal * (discountAmount / 100)
    } else {
      discount = discountAmount
    }
  }

  form.value.total_hours = hours
  form.value.total_amount = hallTotal
  form.value.discount_value = discount
  form.value.net_total = Math.max(0, grossTotal - discount)
}

function addService() {
  form.value.additional_billings.push({ service: '', qty: 1, rate: 0, amount: 0, discount_amount: 0 })
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

    form.value.customer = result.name
    form.value.customer_name = result.customer_name || result.name
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

function onServiceChange(row) {
  const found = services.value.find(s => s.name === row.service)
  if (found) { row.rate = Number(found.rate) || 0; updateServiceRow(row) }
}

function updateServiceRow(row) {
  row.amount = (Number(row.qty) || 0) * (Number(row.rate) || 0)
  computeTotals()
}

async function save(submit) {
  if (!canSave.value) return

  saving.value = true
  error.value = null

  try {
    const payload = {
      ...form.value,
      mobile_number: normalizePhone(form.value.mobile_number),
      submit
    }

    const result = await callMethod(
      'rhohotel.rhocom_hotel.api.hall_booking.create_booking',
      {
        data: JSON.stringify(payload)
      }
    )

    router.push(`/hall/booking/${result.name}`)
  } catch(e) {
    error.value = e.message || 'Failed to save booking.'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const [h, s, c, items] = await Promise.all([
      callMethod('rhohotel.rhocom_hotel.api.hall_booking.get_halls'),
      callMethod('rhohotel.rhocom_hotel.api.hall_booking.get_services'),
      callMethod('rhohotel.rhocom_hotel.api.hall_booking.get_customers'),
      callMethod('rhohotel.rhocom_hotel.api.hall.get_all_items')
    ])

    halls.value = h || []
    services.value = s || []
    customers.value = c || []
    allItems.value = items || []

    // PREFILL HALL WHEN COMING FROM HALL DETAIL PAGE
    if (route.query.hall) {
      form.value.hall = route.query.hall
      await onHallChange()
    }

  } catch(e) {
    console.error(e)
  }
})

async function searchCustomers() {
  const data = await callMethod(
    'rhohotel.rhocom_hotel.api.hall_booking.search_customers',
    { query: customerSearch.value }
  )

  customers.value = data || []
  showCustomerDropdown.value = true
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

function onServiceItemChange() {
  const found = allItems.value.find(i => i.item_code === serviceForm.value.item_name)

  if (found) {
    serviceForm.value.service = found.item_name
  } else {
    serviceForm.value.service = serviceForm.value.item_name
  }
}

async function createHallService() {
  if (!serviceForm.value.item_name) return

  const created = await callMethod(
    'rhohotel.rhocom_hotel.api.hall_booking.create_hall_service',
    {
      data: JSON.stringify({
        item_name: serviceForm.value.item_name,
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

async function searchItems() {
  const data = await callMethod(
    'rhohotel.rhocom_hotel.api.hall_booking.search_items',
    { query: itemSearch.value || '' }
  )

  itemResults.value = data || []
  showItemDropdown.value = true
}
function selectServiceItem(i) {
  serviceForm.value.item_name = i.item_code
  serviceForm.value.service = i.item_name || i.item_code
  itemSearch.value = i.item_name || i.item_code
  showItemDropdown.value = false
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

</script>