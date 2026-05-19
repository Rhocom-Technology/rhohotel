<template>
  <Teleport to="body">
    <div v-if="modelValue"
      class="modal-enter fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('update:modelValue', false)">
      <div class="modal-panel bg-white rounded-2xl w-full shadow-2xl overflow-hidden flex flex-col" style="max-width:1000px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-6 border-b border-gray-100">
          <div class="flex items-start justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-900">Draft Orders</h2>
              <p class="text-xs text-gray-400 mt-1">Review saved POS drafts, resume suspended bills, reassign service points, or delete old drafts before checkout.</p>
            </div>
            <button @click="$emit('update:modelValue', false)"
              class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-sm ml-4 flex-shrink-0">✕</button>
          </div>
          <div class="flex items-center gap-2 mt-5">
              <p v-if="actionError" class="text-xs text-red-500 flex-1">{{ actionError }}</p>
            <button @click="deleteDraft" :disabled="!selectedDraft || deleting"
              class="btn-hover px-4 py-2 text-xs font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed">
              {{ deleting ? 'Deleting…' : 'Delete Draft' }}
            </button>
            <button @click="$emit('update:modelValue', false)" class="btn-hover px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Close Page</button>
            <button @click="printDraftBill" :disabled="!selectedDraft"
              class="btn-hover px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed">Print Draft Bill</button>
            <button @click="resumeDraft" :disabled="!selectedDraft || resuming"
              class="btn-hover px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed">
              {{ resuming ? 'Loading…' : 'Resume Draft' }}
            </button>
          </div>
        </div>

        <div class="overflow-y-auto flex-1 px-8 py-6 space-y-6">
          <!-- Filters -->
          <div class="bg-gray-50 rounded-xl border border-gray-200 p-5">
            <h4 class="text-xs font-bold text-gray-700 mb-4">Filters & Search</h4>
            <div class="flex items-end gap-3 flex-wrap">
              <div class="flex-1 min-w-40">
                <p class="text-xs text-gray-500 mb-1.5">Search draft</p>
                <div class="relative">
                  <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                  <input v-model="draftSearch" type="text" placeholder="Invoice no., room, table, cashier..."
                    class="w-full pl-8 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>
              <div class="min-w-36">
                <p class="text-xs text-gray-500 mb-1.5">Service Point</p>
                <select v-model="draftFilterPoint" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-gray-700">
                  <option value="">All Points</option>
                  <option v-for="pt in availableServicePoints" :key="pt">{{ pt }}</option>
                </select>
              </div>
              <div class="min-w-36">
                <p class="text-xs text-gray-500 mb-1.5">Cashier</p>
                <select v-model="draftFilterCashier" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none bg-white text-gray-700">
                  <option value="">All Cashiers</option>
                  <option v-for="c in availableCashiers" :key="c">{{ c }}</option>
                </select>
              </div>
              <button @click="draftSearch='';draftFilterPoint='';draftFilterCashier='';draftPage=1"
                class="btn-hover px-4 py-2.5 text-xs font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-100 bg-white">Reset</button>
              <button @click="$emit('update:modelValue', false)" class="btn-hover px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">Create New Draft</button>
            </div>
          </div>

          <!-- Stats -->
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
            <div v-for="s in draftStats" :key="s.label" class="bg-white rounded-xl border border-gray-200 px-6 py-5">
              <p class="text-xs text-gray-400 mb-2">{{ s.label }}</p>
              <p class="text-2xl font-bold text-gray-900">{{ s.value }}</p>
            </div>
          </div>

          <!-- List + selected -->
          <div style="display:grid;grid-template-columns:1fr 320px;gap:16px;">
            <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                <h4 class="text-xs font-bold text-gray-900">Saved Draft Orders</h4>
                <p class="text-xs text-gray-400">Showing {{ draftPageStart + 1 }}–{{ draftPageEnd }} of {{ filteredDrafts.length }} drafts</p>
              </div>
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-100 bg-gray-50">
                    <th class="text-left text-xs font-medium text-gray-500 px-6 py-3.5">Invoice No.</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Service Point</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Cashier</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Items</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Amount</th>
                    <th class="text-left text-xs font-medium text-gray-500 px-4 py-3.5">Age</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="d in pagedDrafts" :key="d.id"
                    @click="selectedDraft = d"
                    class="table-row cursor-pointer border-b border-gray-50 last:border-0"
                    :class="selectedDraft?.id === d.id ? 'bg-blue-50' : 'bg-white hover:bg-gray-50'">
                    <td class="px-6 py-4 text-xs font-semibold text-blue-600">{{ d.invoice }}</td>
                    <td class="px-4 py-4 text-xs text-gray-600">{{ d.point }}</td>
                    <td class="px-4 py-4 text-xs text-gray-600">{{ d.cashier }}</td>
                    <td class="px-4 py-4 text-xs text-gray-700">{{ d.items }}</td>
                    <td class="px-4 py-4 text-xs font-semibold text-gray-900">₦{{ d.amount.toLocaleString() }}</td>
                    <td class="px-4 py-4 text-xs font-semibold" :class="d.ageMinutes > 60 ? 'text-orange-500' : 'text-amber-400'">{{ d.age }}</td>
                  </tr>
                </tbody>
              </table>
              <!-- Pagination -->
              <div v-if="draftTotalPages > 1" class="flex items-center justify-between px-6 py-3 border-t border-gray-100 bg-gray-50">
                <p class="text-xs text-gray-400">Page {{ draftPage }} of {{ draftTotalPages }}</p>
                <div class="flex items-center gap-1">
                  <button @click="draftPage--" :disabled="draftPage === 1"
                    class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed bg-white transition-colors">← Prev</button>
                  <button v-for="p in draftTotalPages" :key="p" @click="draftPage = p"
                    class="w-7 h-7 flex items-center justify-center text-xs rounded-lg transition-colors"
                    :class="draftPage === p ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-white border border-gray-200 bg-transparent'">{{ p }}</button>
                  <button @click="draftPage++" :disabled="draftPage === draftTotalPages"
                    class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed bg-white transition-colors">Next →</button>
                </div>
              </div>
            </div>

            <div v-if="selectedDraft" class="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
              <div class="px-6 py-4 border-b border-gray-200 bg-white">
                <h4 class="text-xs font-bold text-gray-900">Selected Draft</h4>
              </div>
              <div class="p-6 space-y-3 text-xs">
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Invoice No.</span><span class="font-bold text-gray-900">{{ selectedDraft.invoice }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Service Point</span><span class="font-semibold text-gray-900">{{ selectedDraft.detailPoint }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Cashier</span><span class="font-semibold text-gray-900">{{ selectedDraft.cashier }}</span></div>
                <div class="flex justify-between py-1.5 border-b border-gray-100"><span class="text-gray-400">Saved At</span><span class="font-semibold text-gray-900">{{ selectedDraft.savedAt }}</span></div>
                <div class="flex justify-between py-1.5"><span class="text-gray-400">Total Value</span><span class="font-bold text-blue-600">₦{{ selectedDraft.amount.toLocaleString() }}</span></div>
              </div>
              <div class="mx-6 mb-5 bg-white rounded-xl border border-gray-200 p-4">
                <p class="text-xs font-bold text-gray-900 mb-3">Draft Items</p>
                <div v-for="item in selectedDraft.draftItems" :key="item.name"
                  class="flex justify-between text-xs py-2 border-b border-gray-50 last:border-0">
                  <span class="text-gray-600">{{ item.name }}</span>
                  <span class="font-semibold text-gray-900">× {{ item.qty }}</span>
                </div>
              </div>
              <div class="px-6 pb-6">
                <p class="text-xs font-bold text-gray-900 mb-2">Draft Note</p>
                <div class="bg-white rounded-xl border border-gray-200 p-4 text-xs text-gray-500 leading-relaxed min-h-12">
                  {{ selectedDraft.note || 'No note added.' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'

const props = defineProps({
  modelValue: Boolean,
})
const emit = defineEmits(['update:modelValue', 'resume'])

const draftSearch = ref('')
const draftFilterPoint = ref('')
const draftFilterCashier = ref('')
const draftPage = ref(1)
const perPage = 10
const selectedDraft = ref(null)

const resuming = ref(false)
const deleting = ref(false)
const actionError = ref('')

// ── API: Draft Orders ──────────────────────────────────────────────────────
const draftsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_draft_pos_invoices',
  auto: true,
})

const statsResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_draft_pos_stats',
  auto: true,
})

let searchTimer = null
watch([draftSearch, draftFilterPoint, draftFilterCashier], () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    draftsResource.params = {
      search: draftSearch.value || null,
      cashier: draftFilterCashier.value || null,
    }
    draftsResource.reload()
  }, 300)
})

// ── Computed ───────────────────────────────────────────────────────────────
const allDrafts = computed(() => {
  return (draftsResource.data || []).map(d => ({
    id: d.invoice,
    invoice: d.invoice,
    point: d.service_point || d.pos_profile || d.customer || '—',
    cashier: d.cashier,
    items: d.item_count || 0,
    amount: Number(d.amount) || 0,
    age: d.age || '0m',
    ageMinutes: d.age_minutes || 0,
    savedAt: d.posting_date || '',
    detailPoint: d.service_point || d.pos_profile || d.customer || '—',
    draftItems: d.items || [],
    note: d.note || '',
  }))
})

const filteredDrafts = computed(() => {
  let data = allDrafts.value
  if (draftSearch.value) {
    const q = draftSearch.value.toLowerCase()
    data = data.filter(d =>
      d.invoice.toLowerCase().includes(q) ||
      d.point.toLowerCase().includes(q) ||
      d.cashier.toLowerCase().includes(q)
    )
  }
  if (draftFilterPoint.value) data = data.filter(d => d.point === draftFilterPoint.value)
  if (draftFilterCashier.value) data = data.filter(d => d.cashier === draftFilterCashier.value)
  return data
})

// Dynamic filter options derived from actual data
const availableServicePoints = computed(() => [...new Set(allDrafts.value.map(d => d.point).filter(Boolean))])
const availableCashiers = computed(() => [...new Set(allDrafts.value.map(d => d.cashier).filter(Boolean))])

const draftStats = computed(() => {
  const s = statsResource.data || {}
  const total = Number(s.total_drafts || 0)
  const oldest = Number(s.oldest_minutes || 0)
  const h = Math.floor(oldest / 60)
  const m = oldest % 60
  return [
    { label: 'Total Draft Orders', value: String(total) },
    { label: 'Total Value', value: `₦${Number(s.total_value || 0).toLocaleString()}` },
    { label: 'Open Drafts', value: String(total) },
    { label: 'Oldest Pending', value: h ? `${h}h ${m}m` : `${m}m` },
  ]
})

const draftTotalPages = computed(() => Math.max(1, Math.ceil(filteredDrafts.value.length / perPage)))
const draftPageStart = computed(() => (draftPage.value - 1) * perPage)
const draftPageEnd = computed(() => Math.min(draftPageStart.value + perPage, filteredDrafts.value.length))
const pagedDrafts = computed(() => filteredDrafts.value.slice(draftPageStart.value, draftPageEnd.value))

watch(filteredDrafts, () => { draftPage.value = 1 })

// ── Actions ────────────────────────────────────────────────────────────────
const resumeResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.get_pos_draft_invoice_detail',
  onSuccess(data) {
    resuming.value = false
    emit('resume', data)
    emit('update:modelValue', false)
  },
  onError(err) {
    resuming.value = false
    actionError.value = err?.message || 'Failed to load draft'
    setTimeout(() => { actionError.value = '' }, 4000)
  },
})

const deleteResource = createResource({
  url: 'rhohotel.rhocom_hotel.api.pos.delete_pos_draft_invoice',
  onSuccess() {
    deleting.value = false
    selectedDraft.value = null
    draftsResource.reload()
    statsResource.reload()
  },
  onError(err) {
    deleting.value = false
    actionError.value = err?.message || 'Failed to delete draft'
    setTimeout(() => { actionError.value = '' }, 4000)
  },
})

function resumeDraft() {
  if (!selectedDraft.value || resuming.value) return
  resuming.value = true
  resumeResource.submit({ invoice_name: selectedDraft.value.invoice })
}

function deleteDraft() {
  if (!selectedDraft.value || deleting.value) return
  if (!confirm(`Delete draft ${selectedDraft.value.invoice}? This cannot be undone.`)) return
  deleting.value = true
  deleteResource.submit({ invoice_name: selectedDraft.value.invoice })
}

function printDraftBill() {
  if (!selectedDraft.value) return
  window.open(
    `/printview?doctype=POS%20Invoice&name=${encodeURIComponent(selectedDraft.value.invoice)}&trigger_print=1`,
    '_blank'
  )
}
</script>

<style>
@keyframes modalIn {
  from { opacity: 0; transform: scale(0.96) translateY(8px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}
@keyframes overlayIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.modal-enter { animation: overlayIn 0.2s ease; }
.modal-panel { animation: modalIn 0.25s cubic-bezier(0.34,1.56,0.64,1); }
.btn-hover { transition: all 0.15s ease; }
.btn-hover:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.btn-hover:active { transform: translateY(0); }
.table-row { transition: background 0.15s ease; }
</style>