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
            v-for="child in group.children"
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
import { ref } from 'vue'
import {
  ChevronDown, LayoutGrid, Sparkles, Wrench,
  CreditCard, BarChart2, ShoppingCart, UtensilsCrossed,
  Gift, Settings
} from 'lucide-vue-next'

const openGroups = ref(['Front Desk'])

function toggleGroup(label) {
  const index = openGroups.value.indexOf(label)
  if (index === -1) {
    openGroups.value.push(label)
  } else {
    openGroups.value.splice(index, 1)
  }
}

const navGroups = [
  {
    label: 'Front Desk',
    icon: LayoutGrid,
    children: [
      { label: 'Room View', to: '/room-view' },
      { label: 'Check-ins', to: '/check-ins' },
      { label: 'Check-outs', to: '/check-outs' },
      { label: 'Reservations', to: '/reservations' },
      { label: 'Payments', to: '/payments' },
      { label: 'Guest List', to: '/guests' },
      { label: 'Night Audit', to: '/night-audit' },
    ],
  },
  {
    label: 'Rooms',
    icon: LayoutGrid,
    children: [
      { label: 'Room List', to: '/rooms' },
    ],
  },
  {
    label: 'Housekeeping',
    icon: Sparkles,
    children: [
      { label: 'Dashboard', to: '/housekeeping/dashboard' },
      { label: 'Task List', to: '/housekeeping' },
      { label: 'Housekeeping Report', to: '/housekeeping/report' },
    ],
  },
  {
    label: 'Maintenance',
    icon: Wrench,
    children: [
      { label: 'Maintenance List', to: '/maintenance/list' },
      { label: 'Dashboard', to: '/maintenance/dashboard' },
      { label: 'Request', to: '/maintenance/request' },
      { label: 'Technician List', to: '/maintenance/technicians' },
    ],
  },
  {
    label: 'Billing',
    icon: CreditCard,
    children: [
      { label: 'Billing Dashboard', to: '/billing' },
      { label: 'Corporate Billing', to: '/billing/corporate' },
      { label: 'Bill Transfers',    to: '/billing/bill-transfers' },
    ],
  },
  {
    label: 'Reports',
    icon: BarChart2,
    children: [
      { label: 'Report List',                    to: '/reports' },
      { label: 'Daily Occupancy Report',         to: '/reports/daily-occupancy-report' },
      { label: 'Guest Stay History Report',      to: '/reports/guest-stay-history-report' },
      { label: 'Night Audit Summary Report',    to: '/reports/night-audit-summary-report' },
      { label: 'Corporate Account Statement', to: '/reports/corporate-account-statement' },
      { label: 'Corporate Billing Statement', to: '/reports/corporate-billing-statement' },
      { label: 'POS Sales Report', to: '/reports/pos-sales-report' },
      { label: 'Housekeeping Productivity Report', to: '/reports/house-keeping-productivity-report' },
    ],
  },
  {
    label: 'Point of Sales',
    icon: ShoppingCart,
    children: [
      { label: 'POS Dashboard', to: '/pos' },
      { label: 'Manager Dashboard', to: '/pos/manager-dashboard' },   
      { label: 'POS Invoice List', to: '/pos/invoices' },
      { label: 'Shift Difference Log', to: '/pos/shift-difference-log' }, 
    ],
  },
  {
    label: 'Staff Roaster',
    icon: ShoppingCart,
    to: '/pos/staff-roaster',
  },
  {
    label: 'Kitchen Terminal',
    icon: UtensilsCrossed,
    children: [
      { label: 'Kitchen Dashboard', to: '/kitchen' },
    ],
  },
  {
    label: 'Complimentary Mgmt',
    icon: Gift,
    children: [
       { label: 'Dashboard',             to: '/complimentary' },
        { label: 'Complimentary List',    to: '/complimentary/list' },
        { label: 'New Complimentary',     to: '/complimentary/new' },
    ],
  },
  
  {
    label: 'Asset Management',
    icon: Settings,
    children: [
     { label: 'Dashboard',  to: '/assets-mgmt' },
  { label: 'Asset List', to: '/assets-mgmt/list' },
  { label: 'Asset Maintenance', to: '/assets-mgmt/maintenance' },
    ],
  },
]
</script>