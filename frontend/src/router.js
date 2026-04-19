import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from '@/stores/session'

const router = createRouter({
  history: createWebHistory('/app/front-desk'),
  routes: [
    { path: '/login', name: 'Login', component: () => import('@/pages/Login.vue') },
    { path: '/', redirect: '/room-view' },

    // ── Front Desk ──────────────────────────────────────
    { path: '/room-view', name: 'RoomView', component: () => import('@/pages/frontdesk/RoomView.vue') },
    { path: '/check-ins', name: 'CheckIns', component: () => import('@/pages/frontdesk/CheckIns.vue') },
    { path: '/check-outs', name: 'CheckOuts', component: () => import('@/pages/frontdesk/CheckOuts.vue') },
    { path: '/reservations', name: 'Reservations', component: () => import('@/pages/frontdesk/Reservations.vue') },
    { path: '/reservations/new', name: 'NewReservation', component: () => import('@/pages/frontdesk/NewReservation.vue') },
    { path: '/reservations/:id', name: 'SavedReservation', component: () => import('@/pages/frontdesk/SavedReservation.vue') },
    { path: '/payments', name: 'Payments', component: () => import('@/pages/frontdesk/Payments.vue') },
    { path: '/night-audit', name: 'NightAudit', component: () => import('@/pages/frontdesk/NightAudit.vue') },

    // ── Housekeeping ─────────────────────────────────────
    { path: '/housekeeping', name: 'Housekeeping', component: () => import('@/pages/housekeeping/Housekeeping.vue') },
    { path: '/housekeeping/dashboard', name: 'HousekeepingDashboard', component: () => import('@/pages/housekeeping/HousekeepingDashboard.vue') },
    { path: '/housekeeping/task/new', name: 'NewHousekeepingTask', component: () => import('@/pages/housekeeping/HousekeepingTask.vue') },
    { path: '/housekeeping/task/:id', name: 'HousekeepingTask', component: () => import('@/pages/housekeeping/HousekeepingTask.vue') },
    { path: '/housekeeping/report', name: 'HousekeepingReport', component: () => import('@/pages/housekeeping/HousekeepingReport.vue') },

    // ── Maintenance ──────────────────────────────────────
    { path: '/maintenance/list', name: 'MaintenanceList', component: () => import('@/pages/maintenance/MaintenanceList.vue') },
    { path: '/maintenance/dashboard', name: 'MaintenanceDashboard', component: () => import('@/pages/maintenance/MaintenanceDashboard.vue') },
    { path: '/maintenance/request', name: 'MaintenanceRequest', component: () => import('@/pages/maintenance/MaintenanceRequest.vue') },
    { path: '/maintenance/new-request', name: 'NewMaintenanceRequest', component: () => import('@/pages/maintenance/NewMaintenanceRequest.vue') },
    { path: '/maintenance/request/:id', name: 'SavedMaintenanceRequest', component: () => import('@/pages/maintenance/SavedMaintenanceRequest.vue') },
    { path: '/maintenance/task/:id', name: 'MaintenanceTask', component: () => import('@/pages/maintenance/MaintenanceTask.vue') },
    { path: '/maintenance/new-task', name: 'NewMaintenanceTask', component: () => import('@/pages/maintenance/NewMaintenanceTask.vue') },
    { path: '/maintenance/technicians', name: 'TechnicianList', component: () => import('@/pages/maintenance/TechnicianList.vue') },
    { path: '/maintenance/technicians/:id', name: 'TechnicianView', component: () => import('@/pages/maintenance/TechnicianView.vue') },
    { path: '/maintenance/new-technician', name: 'NewTechnician', component: () => import('@/pages/maintenance/NewTechnician.vue') },

    // ── Billing ──────────────────────────────────────────
    { path: '/billing', name: 'Billing', component: () => import('@/pages/billing/Billing.vue') },

    // ── Reports ──────────────────────────────────────────
    { path: '/reports', name: 'Reports', component: () => import('@/pages/reports/Reports.vue') },

    // ── POS ──────────────────────────────────────────────
    { path: '/pos', name: 'PointOfSales', component: () => import('@/pages/pos/PointOfSales.vue') },

    // ── Kitchen ──────────────────────────────────────────
    { path: '/kitchen', name: 'KitchenTerminal', component: () => import('@/pages/kitchen/KitchenTerminal.vue') },

    // ── Complimentary ─────────────────────────────────────
    { path: '/complimentary', name: 'Complimentary', component: () => import('@/pages/complimentary/Complimentary.vue') },

    // ── Assets ───────────────────────────────────────────
    { path: '/assets-mgmt', name: 'AssetManagement', component: () => import('@/pages/assets/AssetManagement.vue') },
  ],
})

router.beforeEach((to, from, next) => {
  const session = useSessionStore()
  if (to.name !== 'Login' && !session.isLoggedIn) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && session.isLoggedIn) {
    next({ name: 'RoomView' })
  } else {
    next()
  }
})

export default router