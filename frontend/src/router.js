import { createWebHistory } from 'vue-router'
import { createRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { getRequiredRoles, getFirstAllowedRoute } from '@/lib/permissions'

const router = createRouter({
  history: createWebHistory('/frontdesk/'),
  routes: [
    { path: '/', redirect: '/room-view' },
    { path: '/login', name: 'Login', component: () => import('@/pages/Login.vue') },

    // Front Desk
    { path: '/room-view', name: 'RoomView', component: () => import('@/pages/frontdesk/RoomView.vue') },
    { path: '/available-rooms', name: 'AvailableRooms', component: () => import('@/pages/frontdesk/AvailableRooms.vue') },
    { path: '/check-ins', name: 'CheckIns', component: () => import('@/pages/frontdesk/CheckIns.vue') },
    { path: '/check-ins/new', name: 'NewCheckIn', component: () => import('@/pages/frontdesk/NewCheckIn.vue') },
    { path: '/check-ins/:id', name: 'CheckInDetail', component: () => import('@/pages/frontdesk/CheckInDetail.vue') },

    { path: '/check-outs', name: 'CheckOuts', component: () => import('@/pages/frontdesk/CheckOuts.vue') },
    { path: '/check-outs/overdue', name: 'CheckOutOverdue', component: () => import('@/pages/frontdesk/CheckOutOverdue.vue') },
    { path: '/check-outs/:id', name: 'CheckOut', component: () => import('@/pages/frontdesk/CheckoutDetail.vue') },
    { path: '/reservations', name: 'Reservations', component: () => import('@/pages/frontdesk/Reservations.vue') },
    { path: '/reservations/new', name: 'NewReservation', component: () => import('@/pages/frontdesk/NewReservation.vue') },
    { path: '/reservations/:id', name: 'SavedReservation', component: () => import('@/pages/frontdesk/SavedReservation.vue') },
    { path: '/payments', name: 'Payments', component: () => import('@/pages/frontdesk/Payments.vue') },
    { path: '/guests', name: 'GuestList', component: () => import('@/pages/frontdesk/GuestList.vue') },
    { path: '/night-audit', name: 'NightAudit', component: () => import('@/pages/frontdesk/NightAudit.vue') },

    { path: '/guests/new', name: 'NewGuest', component: () => import('@/pages/frontdesk/NewGuest.vue') },
    { path: '/guests/:id', name: 'GuestProfile', component: () => import('@/pages/frontdesk/GuestProfile.vue') },
    { path: '/guests/:id/edit', name: 'EditGuest', component: () => import('@/pages/frontdesk/EditGuest.vue') },

    { path: '/weekly-shift-generator', name: 'WeeklyShiftGenerator', component: () => import('@/pages/shift/WeeklyShiftGenerator.vue') },
    { path: '/shift-list', name: 'ShiftList', component: () => import('@/pages/shift/ShiftList.vue') },
    { path: '/swap-requests', name: 'SwapRequestList', component: () => import('@/pages/shift/SwapRequestList.vue') },
    { path: '/shift-preference', name: 'StaffShiftPreference', component: () => import('@/pages/shift/StaffShiftPreference.vue') },
    { path: '/staff-roaster-dashboard', name: 'StaffRoasterDashboard', component: () => import('@/pages/shift/StaffRoasterDashboard.vue') },

    // Housekeeping
    { path: '/housekeeping', name: 'Housekeeping', component: () => import('@/pages/housekeeping/Housekeeping.vue') },
    { path: '/housekeeping/dashboard', name: 'HousekeepingDashboard', component: () => import('@/pages/housekeeping/HousekeepingDashboard.vue') },
    { path: '/housekeeping/task/new', name: 'NewHousekeepingTask', component: () => import('@/pages/housekeeping/NewHousekeepingTask.vue') },
    { path: '/housekeeping/task/:id', name: 'HousekeepingTask', component: () => import('@/pages/housekeeping/HousekeepingTask.vue') },
    { path: '/housekeeping/report', name: 'HousekeepingReport', component: () => import('@/pages/housekeeping/HousekeepingReport.vue') },
    { path: '/shift-preference-manager', name: 'StaffShiftPreferenceManagerView', component: () => import('@/pages/shift/StaffShiftPreferenceManagerView.vue') },

    // Maintenance
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

    // POS
    { path: '/pos', name: 'PointOfSales', component: () => import('@/pages/pos/PointOfSales.vue') },
    { path: '/pos/shift-close', name: 'POSShiftClose', component: () => import('@/pages/pos/POSShiftClose.vue') },
    { path: '/pos/invoices', name: 'POSInvoiceList', component: () => import('@/pages/pos/POSInvoiceList.vue') },
    { path: '/pos/manager-dashboard', name: 'POSManagerDashboard', component: () => import('@/pages/pos/POSManagerDashboard.vue') },
    { path: '/pos/shift-difference-log', name: 'POSShiftDifferenceLog', component: () => import('@/pages/pos/ShiftDifferenceLog.vue') },
    { path: '/pos/staff-roaster', name: 'StaffRoasterPage', component: () => import('@/pages/pos/StaffRoasterPage.vue') },

    // Kitchen
    { path: '/kitchen', name: 'KitchenTerminal', component: () => import('@/pages/kitchen/KitchenTerminal.vue') },


    // Complimentary
    { path: '/complimentary', name: 'Complimentary', component: () => import('@/pages/complimentary/Complimentary.vue') },
    { path: '/complimentary/list', name: 'ComplimentaryList', component: () => import('@/pages/complimentary/ComplimentaryList.vue') },
    { path: '/complimentary/new', name: 'NewComplimentary', component: () => import('@/pages/complimentary/NewComplimentary.vue') },
    { path: '/complimentary/:id', name: 'SavedComplimentary', component: () => import('@/pages/complimentary/SavedComplimentary.vue') },

    // Asset Management
    { path: '/assets-mgmt', name: 'AssetManagement', component: () => import('@/pages/assets/AssetManagement.vue') },
    { path: '/assets-mgmt/list', name: 'AssetList', component: () => import('@/pages/assets/AssetList.vue') },
    { path: '/assets-mgmt/asset/:id', name: 'SavedAsset', component: () => import('@/pages/assets/SavedAsset.vue') },
    { path: '/assets-mgmt/maintenance', name: 'AssetMaintenance', component: () => import('@/pages/assets/AssetMaintenance.vue') },
    { path: '/assets-mgmt/maintenance/new', name: 'NewAssetMaintenance', component: () => import('@/pages/assets/NewAssetMaintenance.vue') },
    { path: '/assets-mgmt/maintenance/:id', name: 'SavedAssetMaintenance', component: () => import('@/pages/assets/SavedAssetMaintenance.vue') },

    // Billing
    { path: '/billing', name: 'Billing', component: () => import('@/pages/billing/Billing.vue') },
    { path: '/billing/payments', name: 'PaymentList', component: () => import('@/pages/billing/PaymentList.vue') },
    { path: '/billing/invoices', name: 'InvoiceList', component: () => import('@/pages/billing/InvoiceList.vue') },
    { path: '/billing/reconcile', name: 'BillingReconcile', component: () => import('@/pages/billing/BillingReconcile.vue') },
    { path: '/billing/corporate', name: 'CorporateBillList', component: () => import('@/pages/billing/CorporateBillList.vue') },
    { path: '/billing/corporate/:id', name: 'CorporateBillDetail', component: () => import('@/pages/billing/CorporateBillDetail.vue') },
    { path: '/billing/bill-transfers', name: 'BillTransferList', component: () => import('@/pages/billing/BillTransferList.vue') },

    // Rooms
    { path: '/rooms', name: 'RoomList', component: () => import('@/pages/rooms/RoomList.vue') },
    { path: '/rooms/new', name: 'NewRoom', component: () => import('@/pages/rooms/NewRoom.vue') },
    { path: '/rooms/:id', name: 'SavedRoom', component: () => import('@/pages/frontdesk/SavedRoom.vue') },


    // Hall Management
    { path: '/hall',                  name: 'HallList',         component: () => import('@/pages/hall/HallList.vue') },
    { path: '/hall-dashboard',                  name: 'Hall Dashboard',         component: () => import('@/pages/hall/HallDashboard.vue') },
    { path: '/hall/new',              name: 'NewHall',          component: () => import('@/pages/hall/NewHall.vue') },
    { path: '/hall/booking',          name: 'HallBookingList',  component: () => import('@/pages/hall/HallBookingList.vue') },
    { path: '/hall/booking/new',      name: 'NewHallBooking',   component: () => import('@/pages/hall/NewHallBooking.vue') },
    { path: '/hall/booking/:id/edit', name: 'EditHallBooking', component: () => import('@/pages/hall/EditHallBooking.vue') },
    { path: '/hall/booking/:id',      name: 'HallBooking',      component: () => import('@/pages/hall/HallBooking.vue') },
    { path: '/hall/:id',              name: 'SavedHall',        component: () => import('@/pages/hall/SavedHall.vue') },
    { path: '/hall/:id/edit',         name: 'EditHall',         component: () => import('@/pages/hall/NewHall.vue') },

    // Others
    { path: '/reports', name: 'ReportList', component: () => import('@/pages/reports/ReportList.vue') },
    { path: '/reports/corporate-account-statement', name: 'CorporateAccountStatement', component: () => import('@/pages/reports/CorporateAccountStatement.vue') },
    { path: '/reports/daily-occupancy-report', name: 'DailyOccupancyReport', component: () => import('@/pages/reports/DailyOccupancyReport.vue') },
    { path: '/reports/guest-stay-history-report', name: 'GuestStayHistoryReport', component: () => import('@/pages/reports/GuestStayHistory.vue') },
    { path: '/reports/night-audit-summary-report', name: 'NightAuditSummaryReport', component: () => import('@/pages/reports/NightAuditSummaryReport.vue') },
    { path: '/reports/corporate-billing-statement', name: 'CorporateBillingStatementReport', component: () => import('@/pages/reports/CorporateBillingStatementReport.vue') },
    { path: '/reports/complimentary-house-use-report', name: 'ComplimentaryHouseUseReport', component: () => import('@/pages/reports/ComplimentaryHouseUseReport.vue') },
    { path: '/reports/pos-sales-report', name: 'PosSalesReport', component: () => import('@/pages/reports/POSSalesPerformance.vue') },
    { path: '/reports/house-keeping-productivity-report', name: 'HousekeepingProductivityReport', component: () => import('@/pages/reports/HousekeepingProductivityReport.vue') },

  ],
})

router.beforeEach(async (to) => {
  const session = useSessionStore()
  await session.initialize()

  if (to.name !== 'Login' && !session.isLoggedIn) {
    return { name: 'Login' }
  }

  if (to.name === 'Login' && session.isLoggedIn) {
    const landing = getFirstAllowedRoute(session.roles)
    return { path: landing }
  }

  // Role-based authorization check
  if (session.isLoggedIn && to.name !== 'Login') {
    const requiredRoles = getRequiredRoles(to.path)
    if (requiredRoles && !session.hasAnyRole(requiredRoles)) {
      const fallback = getFirstAllowedRoute(session.roles)
      if (fallback === to.path) return true
      return fallback === '/login' ? { name: 'Login' } : { path: fallback }
    }
  }

  return true
})

export default router
