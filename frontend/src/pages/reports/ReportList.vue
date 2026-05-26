<template>
  <div class="space-y-4">

    <!-- Intro text -->
    <p class="text-xs text-gray-500">Browse, filter, preview, export, and print operational and management reports across all hotel modules.</p>

    <!-- Control Center -->
    <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900">Reports Control Center</h3>
          <p class="text-xs text-gray-400 mt-0.5">Use filters to narrow the list and open any report for viewing, printing, or export.</p>
        </div>
        <div class="flex items-center gap-2">
          <!-- Category -->
          <div class="relative">
            <button @click="showCategoryDropdown = !showCategoryDropdown"
              class="flex items-center gap-2 px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 min-w-[120px] justify-between">
              <span>{{ selectedCategory || 'Category' }}</span>
              <svg class="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </button>
            <div v-if="showCategoryDropdown"
              class="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-[160px]">
              <button @click="selectedCategory = ''; showCategoryDropdown = false"
                class="w-full text-left px-3 py-2 text-xs text-gray-700 hover:bg-gray-50">All Categories</button>
              <button v-for="cat in categories" :key="cat" @click="selectedCategory = cat; showCategoryDropdown = false"
                class="w-full text-left px-3 py-2 text-xs text-gray-700 hover:bg-gray-50">{{ cat }}</button>
            </div>
          </div>

          <!-- Search label -->
          <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
            Search
          </button>

          <!-- Search input -->
          <input v-model="searchQuery" type="text" placeholder="Search report name..."
            class="px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 w-48" />

          <!-- Refresh -->
          <button @click="searchQuery = ''; selectedCategory = ''"
            class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
            Refresh
          </button>

          <!-- New Report AI -->
          <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
            New Report AI
          </button>
        </div>
      </div>
    </div>

    <!-- Stats row -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-400">Total Reports</p>
          <span class="px-2.5 py-0.5 text-xs font-semibold bg-blue-100 text-blue-700 rounded-full">Library</span>
        </div>
        <p class="text-3xl font-bold text-gray-900">{{ filteredReports.length }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 px-6 py-5">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-400">Most Used Category</p>
          <span class="px-2.5 py-0.5 text-xs font-semibold bg-purple-100 text-purple-700 rounded-full">Top</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">Front Desk</p>
      </div>
    </div>

    <!-- Report Table -->
    <div class="bg-white rounded-xl border border-gray-200 p-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-bold text-gray-900">Available Reports</h3>
        <p class="text-xs text-gray-400">{{ filteredReports.length }} records</p>
      </div>

      <!-- Table header -->
      <div style="display:grid;grid-template-columns:2fr 1.2fr 2.5fr 1fr;gap:12px;"
        class="px-3 py-2 border-b border-gray-100 mb-1">
        <p class="text-xs font-semibold text-blue-500">Report Name</p>
        <p class="text-xs font-semibold text-blue-500">Category</p>
        <p class="text-xs font-semibold text-blue-500">Description</p>
        <p class="text-xs font-semibold text-blue-500 text-right">Actions</p>
      </div>

      <!-- Rows -->
      <div v-for="report in filteredReports" :key="report.name"
        class="border-b border-gray-100 last:border-0">
        <div style="display:grid;grid-template-columns:2fr 1.2fr 2.5fr 1fr;gap:12px;"
          class="px-3 py-4 items-center hover:bg-gray-50 rounded-lg transition-colors">

          <!-- Name + subtitle -->
          <div>
            <p class="text-xs font-semibold text-gray-900">{{ report.name }}</p>
            <p class="text-[10px] text-gray-400 mt-0.5 leading-relaxed">{{ report.subtitle }}</p>
          </div>

          <!-- Category -->
          <p class="text-xs text-gray-600">{{ report.category }}</p>

          <!-- Description -->
          <div>
            <p class="text-xs text-gray-700">{{ report.description }}</p>
            <p class="text-[10px] text-gray-400 mt-0.5">{{ report.exportNote }}</p>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-1.5 justify-end">
             <button @click="viewReport(report)" class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
            View
          </button>
             <button @click="downloadReport(report)" class="px-4 py-2 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">
            Download
          </button>
             <button @click="printReport(report)" class="px-4 py-2 text-xs font-semibold text-white bg-amber-500 rounded-lg hover:bg-amber-600 transition-colors">
            Print
          </button>
            <!-- <button @click="viewReport(report)"
              class="px-2 py-1.5 text-[8px] font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
              View
            </button>
            <button
              class="px-3 py-1.5 text-[10px] font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors">
              Download
            </button>
            <button
              class="px-3 py-1.5 text-[10px] font-semibold text-white bg-amber-500 rounded-lg hover:bg-amber-600 transition-colors">
              Print
            </button> -->
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-if="filteredReports.length === 0" class="text-center py-12">
        <p class="text-xs text-gray-400">No reports match your filters.</p>
      </div>
    </div>

    <div class="flex items-center gap-6 px-1">
  <p class="text-xs text-gray-400">Action keys:</p>
  <div class="flex items-center gap-1.5">
    <span class="px-2 py-0.5 rounded-lg text-[9px] font-bold bg-blue-600 text-white">V</span>
    <span class="text-xs text-gray-500">View</span>
  </div>
  <div class="flex items-center gap-1.5">
    <span class="px-2 py-0.5 rounded-lg text-[9px] font-bold bg-green-600 text-white">D</span>
    <span class="text-xs text-gray-500">Download</span>
  </div>
  <div class="flex items-center gap-1.5">
    <span class="px-2 py-0.5 rounded-lg text-[9px] font-bold bg-amber-500 text-white">P</span>
    <span class="text-xs text-gray-500">Print</span>
  </div>
</div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const searchQuery = ref('')
const selectedCategory = ref('')
const showCategoryDropdown = ref(false)

const categories = [
  'Front Desk',
  'Guest Management',
  'Billing',
  'Point of Sale',
  'Housekeeping',
  'Asset Management',
]

const reports = ref([
  {
    name: 'Daily Occupancy Report',
    subtitle: 'Operational room status, arrivals, departures, occupied rooms, and occupancy summary',
    category: 'Front Desk',
    description: 'Used by management for daily performance review and occupancy decision making.',
    exportNote: 'Export: PDF / Excel',
    route: '/reports/daily-occupancy-report',
  },
  {
    name: 'Guest Stay History Report',
    subtitle: 'Historical stay pattern, repeat visit trend, spend profile, and guest retention view',
    category: 'Guest Management',
    description: 'Supports loyalty, complementary decisions, and guest relationship analysis.',
    exportNote: 'Export: PDF',
    route: '/reports/guest-stay-history-report',
  },
  {
    name: 'Night Audit Summary',
    subtitle: 'Audit closure, revenue checks, shift balance summary, and daily financial validation',
    category: 'Billing',
    description: 'Generated after end-of-day processing and used for finance control and review.',
    exportNote: 'Export: PDF / Excel',
    route: '/reports/night-audit-summary-report',
  },
  {
    name: 'POS Sales Performance',
    subtitle: 'Outlet revenue, cashier performance, item sales trend, and payment method summary',
    category: 'Point of Sale',
    description: 'Tracks restaurant, bar, room-posted sales, and helps management evaluate sales performance.',
    exportNote: 'Export: Excel',
    route: '/reports/pos-sales-report',
  },
  {
    name: 'Housekeeping Productivity Report',
    subtitle: 'Room cleaning output, item replacement, turnaround time, and attendant productivity',
    category: 'Housekeeping',
    description: 'Supports supervisor review, staffing decisions, and daily housekeeping control.',
    exportNote: 'Export: PDF / Excel',
    route: '/reports/house-keeping-productivity-report',
  },
  {
    name: 'Corporate Billing Statement',
    subtitle: 'Corporate invoices, payments, credits, outstanding balances, and account exposure',
    category: 'Billing',
    description: 'Used for client follow-up, receivables monitoring, and corporate collections.',
    exportNote: 'Export: PDF',
    route: '/reports/corporate-billing-statement',
  },
  {
  name: 'Corporate Account Statement',
  subtitle: 'Customer account ledger showing invoices, payments, debits, credits and running balances',
  category: 'Billing',
  description: 'Provides customer-level account summaries, transaction history, outstanding balances, and receivable tracking for corporate clients.',
  exportNote: 'Export: PDF / Excel',
  route: '/reports/corporate-account-statement',
},
])

const filteredReports = computed(() => {
  return reports.value.filter(r => {
    const matchesSearch = !searchQuery.value ||
      r.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      r.category.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesCategory = !selectedCategory.value || r.category === selectedCategory.value
    return matchesSearch && matchesCategory
  })
})

function viewReport(report) {
  if (report.route) {
    router.push(report.route)
  }
}
</script>