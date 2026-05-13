<template>
  <div class="space-y-5">

    <div>
      <p class="text-xs text-gray-400">
        <span class="cursor-pointer hover:text-blue-600" @click="$router.push('/assets-mgmt')">Assets</span>
        • <span class="cursor-pointer hover:text-blue-600" @click="$router.push('/assets-mgmt/list')">Asset List</span>
        • {{ asset?.name || 'Loading...' }}
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 px-6 py-12 text-center">
      <p class="text-xs text-gray-400">Loading asset details...</p>
    </div>

    <!-- Error -->
    <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-xl px-6 py-4 flex items-start gap-2">
      <svg class="w-4 h-4 text-red-500 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
      <p class="text-xs text-red-800 font-medium">{{ errorMessage }}</p>
    </div>

    <template v-if="!loading && asset">

      <!-- Header -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <div class="flex items-center gap-3">
            <h3 class="text-sm font-bold text-gray-900">{{ asset.asset_name }}</h3>
            <span class="px-2.5 py-1 text-xs font-semibold rounded-full" :class="statusClass">
              {{ asset.status || (asset.docstatus === 0 ? 'Draft' : '—') }}
            </span>
          </div>
          <p class="text-xs text-gray-400 mt-0.5">{{ asset.name }} • {{ asset.item_name || asset.item_code }}</p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="$router.push('/assets-mgmt/list')"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Back to List</button>
        </div>
      </div>

      <!-- Asset Info + Company Details -->
      <div class="grid grid-cols-2 gap-5">
        <!-- Left: Asset Details -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Asset Details</h4>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Asset ID</span>
              <span class="text-xs font-medium text-gray-900">{{ asset.name }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Asset Name</span>
              <span class="text-xs font-medium text-gray-900">{{ asset.asset_name }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Item Code</span>
              <span class="text-xs font-medium text-gray-900">{{ asset.item_code || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Item Name</span>
              <span class="text-xs font-medium text-gray-900">{{ asset.item_name || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Category</span>
              <span class="text-xs font-medium text-gray-900">{{ asset.asset_category || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Quantity</span>
              <span class="text-xs font-medium text-gray-900">{{ asset.asset_quantity || 1 }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Maintenance Required</span>
              <span class="text-xs font-medium text-gray-900">{{ asset.maintenance_required ? 'Yes' : 'No' }}</span>
            </div>
          </div>
        </div>

        <!-- Right: Location & Org -->
        <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
          <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Location & Organization</h4>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Company</span>
              <span class="text-xs font-medium text-gray-900">{{ asset.company || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Location</span>
              <span class="text-xs font-medium text-gray-900">{{ asset.location || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Department</span>
              <span class="text-xs font-medium text-gray-900">{{ asset.department || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Custodian</span>
              <span class="text-xs font-medium text-gray-900">{{ asset.custodian_name || asset.custodian || '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-xs text-gray-500">Status</span>
              <span class="text-xs font-semibold" :class="statusTextClass">
                {{ asset.status || (asset.docstatus === 0 ? 'Draft' : '—') }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Purchase & Financials -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Purchase & Financial Details</h4>
        <div class="grid grid-cols-3 gap-6">
          <div class="space-y-3">
            <div>
              <span class="text-xs text-gray-500">Purchase Date</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(asset.purchase_date) }}</p>
            </div>
            <div>
              <span class="text-xs text-gray-500">Available for Use</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(asset.available_for_use_date) }}</p>
            </div>
          </div>
          <div class="space-y-3">
            <div>
              <span class="text-xs text-gray-500">Net Purchase Amount</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ formatCurrency(asset.gross_purchase_amount) }}</p>
            </div>
            <div>
              <span class="text-xs text-gray-500">Calculate Depreciation</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ asset.calculate_depreciation ? 'Yes' : 'No' }}</p>
            </div>
          </div>
          <div class="space-y-3">
            <div v-if="asset.calculate_depreciation">
              <span class="text-xs text-gray-500">Value After Depreciation</span>
              <p class="text-xs font-medium text-gray-900 mt-1">{{ formatCurrency(asset.value_after_depreciation) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Insurance Details -->
      <div v-if="asset.policy_number || asset.insurer || asset.insurance_start_date"
        class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <h4 class="text-xs font-bold text-gray-900 mb-4 uppercase tracking-wider">Insurance Details</h4>
        <div class="grid grid-cols-3 gap-6">
          <div>
            <span class="text-xs text-gray-500">Policy Number</span>
            <p class="text-xs font-medium text-gray-900 mt-1">{{ asset.policy_number || '—' }}</p>
          </div>
          <div>
            <span class="text-xs text-gray-500">Insurer</span>
            <p class="text-xs font-medium text-gray-900 mt-1">{{ asset.insurer || '—' }}</p>
          </div>
          <div>
            <span class="text-xs text-gray-500">Insured Value</span>
            <p class="text-xs font-medium text-gray-900 mt-1">{{ asset.insured_value || '—' }}</p>
          </div>
          <div>
            <span class="text-xs text-gray-500">Start Date</span>
            <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(asset.insurance_start_date) }}</p>
          </div>
          <div>
            <span class="text-xs text-gray-500">End Date</span>
            <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(asset.insurance_end_date) }}</p>
          </div>
        </div>
      </div>

      <!-- Related Records: Repairs & Maintenance -->
      <div class="grid grid-cols-2 gap-5">

        <!-- Linked Repairs -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <h4 class="text-xs font-bold text-gray-900 uppercase tracking-wider">Linked Repairs</h4>
          </div>
          <div v-if="asset.repairs && asset.repairs.length" class="divide-y divide-gray-50">
            <div v-for="r in asset.repairs" :key="r.name"
              class="px-6 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors"
              @click="$router.push(`/assets-mgmt/repair/${r.name}`)">
              <div>
                <p class="text-xs font-semibold text-gray-900">{{ r.name }}</p>
                <p class="text-xs text-gray-400">{{ formatDate(r.failure_date) }}</p>
              </div>
              <span class="px-2 py-0.5 text-xs font-semibold rounded-full" :class="repairStatusClass(r)">
                {{ repairStatusLabel(r) }}
              </span>
            </div>
          </div>
          <div v-else class="px-6 py-4 text-xs text-gray-400">No repairs recorded.</div>
        </div>

        <!-- Linked Maintenance -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <h4 class="text-xs font-bold text-gray-900 uppercase tracking-wider">Linked Maintenance</h4>
          </div>
          <div v-if="asset.maintenances && asset.maintenances.length" class="divide-y divide-gray-50">
            <div v-for="m in asset.maintenances" :key="m.name"
              class="px-6 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors"
              @click="$router.push(`/assets-mgmt/maintenance/${m.name}`)">
              <div>
                <p class="text-xs font-semibold text-gray-900">{{ m.name }}</p>
                <p class="text-xs text-gray-400">{{ formatDate(m.creation) }}</p>
              </div>
              <span class="px-2 py-0.5 text-xs font-semibold rounded-full" :class="maintenanceStatusClass(m)">
                {{ maintenanceStatusLabel(m) }}
              </span>
            </div>
          </div>
          <div v-else class="px-6 py-4 text-xs text-gray-400">No maintenance records.</div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h4 class="text-xs font-bold text-gray-900 uppercase tracking-wider">Recent Activity</h4>
        </div>
        <div v-if="asset.activities && asset.activities.length" class="divide-y divide-gray-50">
          <div v-for="(a, idx) in asset.activities" :key="idx" class="px-6 py-3 flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <p class="text-xs text-gray-700 truncate">{{ a.subject }}</p>
            </div>
            <div class="flex-shrink-0 ml-4 text-right">
              <p class="text-xs text-gray-500">{{ formatDate(a.date) }}</p>
              <p class="text-xs text-gray-400">{{ a.user_name }}</p>
            </div>
          </div>
        </div>
        <div v-else class="px-6 py-4 text-xs text-gray-400">No activity recorded for this asset.</div>
      </div>

      <!-- Meta -->
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <div class="grid grid-cols-3 gap-4">
          <div>
            <span class="text-xs text-gray-500">Created By</span>
            <p class="text-xs font-medium text-gray-900 mt-1">{{ asset.created_by }}</p>
          </div>
          <div>
            <span class="text-xs text-gray-500">Created On</span>
            <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(asset.creation) }}</p>
          </div>
          <div>
            <span class="text-xs text-gray-500">Last Modified</span>
            <p class="text-xs font-medium text-gray-900 mt-1">{{ formatDate(asset.modified) }}</p>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'

const route = useRoute()
const loading = ref(true)
const asset = ref(null)
const errorMessage = ref('')

const statusClass = computed(() => {
  if (!asset.value) return ''
  const s = asset.value.status || (asset.value.docstatus === 0 ? 'Draft' : '')
  return {
    'Draft':                'bg-gray-100 text-gray-500',
    'Submitted':            'bg-green-50 text-green-600',
    'Partially Depreciated':'bg-blue-50 text-blue-600',
    'Fully Depreciated':    'bg-blue-100 text-blue-700',
    'Sold':                 'bg-purple-50 text-purple-600',
    'Scrapped':             'bg-red-50 text-red-500',
    'In Maintenance':       'bg-yellow-50 text-yellow-600',
    'Out of Order':         'bg-red-100 text-red-600',
    'Capitalized':          'bg-indigo-50 text-indigo-600',
  }[s] || 'bg-gray-100 text-gray-500'
})

const statusTextClass = computed(() => {
  if (!asset.value) return ''
  const s = asset.value.status || 'Draft'
  return {
    'Draft': 'text-gray-500',
    'Submitted': 'text-green-600',
    'In Maintenance': 'text-yellow-600',
    'Scrapped': 'text-red-500',
    'Out of Order': 'text-red-600',
  }[s] || 'text-gray-900'
})

function repairStatusLabel(r) {
  if (r.rh_approved === 'Rejected') return 'Rejected'
  if (r.repair_status === 'Completed') return 'Completed'
  if (r.rh_approved === 'Approved') return 'Approved'
  return 'Pending'
}

function repairStatusClass(r) {
  const label = repairStatusLabel(r)
  return {
    'Pending':   'bg-yellow-50 text-yellow-600',
    'Approved':  'bg-green-50 text-green-600',
    'Completed': 'bg-blue-50 text-blue-600',
    'Rejected':  'bg-red-50 text-red-500',
  }[label] || 'bg-gray-100 text-gray-500'
}

function maintenanceStatusLabel(m) {
  if (m.rh_approved === 'Rejected' || m.docstatus === 2) return 'Rejected'
  if (m.rh_approved === 'Approved') return 'Approved'
  return 'Pending'
}

function maintenanceStatusClass(m) {
  const label = maintenanceStatusLabel(m)
  return {
    'Pending':  'bg-yellow-50 text-yellow-600',
    'Approved': 'bg-green-50 text-green-600',
    'Rejected': 'bg-red-50 text-red-500',
  }[label] || 'bg-gray-100 text-gray-500'
}

function fetchAsset() {
  loading.value = true
  const resource = createResource({
    url: 'rhohotel.rhocom_hotel.api.assets.get_asset_detail',
    params: { asset_name: route.params.id },
    onSuccess(data) {
      asset.value = data
      loading.value = false
    },
    onError(err) {
      loading.value = false
      errorMessage.value = err?.messages?.[0] || 'Failed to load asset details.'
    }
  })
  resource.fetch()
}

function formatDate(dt) {
  if (!dt) return '—'
  const d = new Date(dt)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatCurrency(val) {
  if (!val && val !== 0) return '—'
  return new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', minimumFractionDigits: 0 }).format(val)
}

onMounted(() => {
  fetchAsset()
})
</script>
