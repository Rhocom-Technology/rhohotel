<template>
  <aside class="w-56 flex-shrink-0 flex flex-col h-full" style="background-color: #1a1f2e;">
    <!-- Logo -->
    <div class="flex-shrink-0 px-4 flex items-center border-b border-white/10" style="height: 56px;">
      <div>
        <div class="text-white font-bold text-lg leading-tight">rhoHMS</div>
        <div class="text-gray-400 text-xs">Front Desk Operations</div>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 overflow-y-auto px-2 py-3 space-y-1">
      <div v-for="group in navGroups" :key="group.label">
        <button
          v-if="group.children"
          @click="toggleGroup(group.label)"
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium text-white hover:bg-white/10 transition-colors"
        >
          <div class="flex items-center gap-2">
            <component :is="group.icon" class="w-4 h-4 text-gray-400" />
            {{ group.label }}
          </div>
          <ChevronDown
            class="w-3 h-3 text-gray-400 transition-transform duration-200"
            :class="{ 'rotate-180': openGroups.includes(group.label) }"
          />
        </button>

        <div v-if="group.children && openGroups.includes(group.label)" class="mt-1 space-y-0.5">
          <router-link
            v-for="child in visibleChildren(group.children)"
            :key="child.to"
            :to="child.to"
            class="flex items-center px-3 py-2 ml-2 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            active-class="bg-blue-600 text-white hover:bg-blue-600"
          >
            {{ child.label }}
          </router-link>
        </div>

        <router-link
          v-if="!group.children"
          :to="group.to"
          class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-white hover:bg-white/10 transition-colors"
          active-class="bg-blue-600"
        >
          <component :is="group.icon" class="w-4 h-4 text-gray-400" />
          {{ group.label }}
        </router-link>
      </div>
    </nav>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  ChevronDown, LayoutGrid, Sparkles, Wrench,
  CreditCard, BarChart2, ShoppingCart, UtensilsCrossed,
  Gift, Settings
} from 'lucide-vue-next'
import { useSessionStore } from '@/stores/session'
import { ROLE_GROUPS } from '@/lib/permissions'

const session = useSessionStore()

const openGroups = ref(['Front Desk'])

function toggleGroup(label) {
  const index = openGroups.value.indexOf(label)
  if (index === -1) {
    openGroups.value.push(label)
  } else {
    openGroups.value.splice(index, 1)
  }
}

const allNavGroups = [
  {
    label: 'Front Desk',
    icon: LayoutGrid,
    allowedRoles: ROLE_GROUPS.frontDesk,
    children: [
      { label: 'Room View', to: '/room-view' },
      { label: 'Available Rooms', to: '/available-rooms' },
      { label: 'Check-ins', to: '/check-ins' },
      { label: 'Check-outs', to: '/check-outs' },
      { label: 'Reservations', to: '/reservations' },
      { label: 'Payments', to: '/payments' },
      { label: 'Guest List', to: '/guests' },
      { label: 'Night Audit', to: '/night-audit' },
      { label: 'Hall List',     to: '/hall' },
      { label: 'Hall Bookings', to: '/hall/booking' },
      { label: 'Hall Dashboard', to: '/hall-dashboard' },
    ],
  },
  {
    label: 'Rooms',
    icon: LayoutGrid,
    allowedRoles: ROLE_GROUPS.rooms,
    children: [
      { label: 'Room List', to: '/rooms' },
    ],
  },
  {
    label: 'Housekeeping',
    icon: Sparkles,
    allowedRoles: ROLE_GROUPS.housekeepingList,
    children: [
      { label: 'Dashboard', to: '/housekeeping/dashboard', allowedRoles: ROLE_GROUPS.housekeepingFull },
      { label: 'Task List', to: '/housekeeping' },
      { label: 'Housekeeping Report', to: '/housekeeping/report', allowedRoles: ROLE_GROUPS.housekeepingFull },
    ],
  },
  {
    label: 'Maintenance',
    icon: Wrench,
    allowedRoles: ROLE_GROUPS.maintenanceList,
    children: [
      { label: 'Maintenance List', to: '/maintenance/list' },
      { label: 'Dashboard', to: '/maintenance/dashboard', allowedRoles: ROLE_GROUPS.maintenanceFull },
      { label: 'Request', to: '/maintenance/request', allowedRoles: ROLE_GROUPS.maintenanceFull },
      { label: 'Technician List', to: '/maintenance/technicians', allowedRoles: ROLE_GROUPS.maintenanceFull },
    ],
  },
  {
    label: 'Billing',
    icon: CreditCard,
    allowedRoles: ROLE_GROUPS.billing,
    children: [
      { label: 'Billing Dashboard', to: '/billing' },
      { label: 'Corporate Billing', to: '/billing/corporate' },
      { label: 'Bill Transfers',    to: '/billing/bill-transfers' },
    ],
  },
  {
    label: 'Point of Sales',
    icon: ShoppingCart,
    allowedRoles: ROLE_GROUPS.posBasic,
    children: [
      { label: 'POS Dashboard', to: '/pos' },
      { label: 'Manager Dashboard', to: '/pos/manager-dashboard', allowedRoles: ROLE_GROUPS.posManager },
      { label: 'POS Invoice List', to: '/pos/invoices', allowedRoles: ROLE_GROUPS.posManager },
      { label: 'Shift Difference Log', to: '/pos/shift-difference-log', allowedRoles: ROLE_GROUPS.posManager },
    ],
  },
  {
    label: 'Staff Roaster',
    icon: ShoppingCart,
    allowedRoles: ROLE_GROUPS.staffRoasterView,
    children: [
      { label: 'Staff Roaster', to: '/pos/staff-roaster', allowedRoles: ROLE_GROUPS.staffRoasterFull },
      { label: 'Weekly Shift Generator', to: '/weekly-shift-generator', allowedRoles: ROLE_GROUPS.staffRoasterFull },
      { label: 'Shift List', to: '/shift-list' },
      { label: 'Swap Request List', to: '/swap-requests' },
      { label: 'Staff Shift Preference', to: '/shift-preference' },
      { label: 'Shift Preference Manager View', to: '/shift-preference-manager', allowedRoles: ROLE_GROUPS.staffRoasterFull },
      { label: 'Staff Roaster Dashboard', to: '/staff-roaster-dashboard', allowedRoles: ROLE_GROUPS.staffRoasterFull },
    ],
  },
  {
    label: 'Kitchen Terminal',
    icon: UtensilsCrossed,
    allowedRoles: ROLE_GROUPS.kitchen,
    children: [
      { label: 'Kitchen Dashboard', to: '/kitchen' },
    ],
  },
  {
    label: 'Complimentary Mgmt',
    icon: Gift,
    allowedRoles: ROLE_GROUPS.complimentary,
    children: [
       { label: 'Dashboard',             to: '/complimentary' },
        { label: 'Complimentary List',    to: '/complimentary/list' },
        { label: 'New Complimentary',     to: '/complimentary/new' },
    ],
  },
  {
    label: 'Asset Management',
    icon: Settings,
    allowedRoles: ROLE_GROUPS.assetManagement,
    children: [
      { label: 'Dashboard',  to: '/assets-mgmt' },
      { label: 'Asset List', to: '/assets-mgmt/list' },
    ],
  },
  {
    label: 'Reports',
    icon: BarChart2,
    allowedRoles: [...ROLE_GROUPS.reportsFrontDesk, ...ROLE_GROUPS.reportsPos, ...ROLE_GROUPS.reportsHousekeeping],
    children: [
      { label: 'Report List',                    to: '/reports', allowedRoles: [...ROLE_GROUPS.reportsFrontDesk, ...ROLE_GROUPS.reportsPos, ...ROLE_GROUPS.reportsHousekeeping] },
      { label: 'Daily Occupancy Report',         to: '/reports/daily-occupancy-report', allowedRoles: ROLE_GROUPS.reportsFrontDesk },
      { label: 'Guest Stay History Report',      to: '/reports/guest-stay-history-report', allowedRoles: ROLE_GROUPS.reportsFrontDesk },
      { label: 'Night Audit Summary Report',    to: '/reports/night-audit-summary-report', allowedRoles: ROLE_GROUPS.reportsFrontDesk },
      { label: 'Corporate Account Statement', to: '/reports/corporate-account-statement', allowedRoles: ROLE_GROUPS.reportsFrontDesk },
      { label: 'Corporate Billing Statement', to: '/reports/corporate-billing-statement', allowedRoles: ROLE_GROUPS.reportsFrontDesk },
      { label: 'Complimentary & House Use', to: '/reports/complimentary-house-use-report', allowedRoles: ROLE_GROUPS.reportsFrontDesk },
      { label: 'POS Sales Report', to: '/reports/pos-sales-report', allowedRoles: ROLE_GROUPS.reportsPos },
      { label: 'Housekeeping Productivity Report', to: '/reports/house-keeping-productivity-report', allowedRoles: ROLE_GROUPS.reportsHousekeeping },
    ],
  },
]

const navGroups = computed(() =>
  allNavGroups.filter((group) => session.hasAnyRole(group.allowedRoles))
)

function visibleChildren(children) {
  return children.filter((child) => !child.allowedRoles || session.hasAnyRole(child.allowedRoles))
}
</script>
