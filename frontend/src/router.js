import { createWebHistory } from 'vue-router'
import { createRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'

const router = createRouter({
  history: createWebHistory('/frontdesk/'),
  routes: [
    { path: '/', redirect: '/room-view' },
    { path: '/login', name: 'Login', component: () => import('@/pages/Login.vue') },

    // Front Desk
    { path: '/room-view', name: 'RoomView', component: () => import('@/pages/frontdesk/RoomView.vue') },
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

    // Housekeeping
    { path: '/housekeeping', name: 'Housekeeping', component: () => import('@/pages/housekeeping/Housekeeping.vue') },
    { path: '/housekeeping/dashboard', name: 'HousekeepingDashboard', component: () => import('@/pages/housekeeping/HousekeepingDashboard.vue') },
    { path: '/housekeeping/task/new', name: 'NewHousekeepingTask', component: () => import('@/pages/housekeeping/NewHousekeepingTask.vue') },
    { path: '/housekeeping/task/:id', name: 'HousekeepingTask', component: () => import('@/pages/housekeeping/HousekeepingTask.vue') },
    { path: '/housekeeping/report', name: 'HousekeepingReport', component: () => import('@/pages/housekeeping/HousekeepingReport.vue') },

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
    { path: '/assets-mgmt/repair', name: 'AssetRepair', component: () => import('@/pages/assets/AssetRepair.vue') },
    { path: '/assets-mgmt/repair/new', name: 'NewAssetRepair', component: () => import('@/pages/assets/NewAssetRepair.vue') },
    { path: '/assets-mgmt/repair/:id', name: 'SavedAssetRepair', component: () => import('@/pages/assets/SavedAssetRepair.vue') },
    { path: '/assets-mgmt/maintenance', name: 'AssetMaintenance', component: () => import('@/pages/assets/AssetMaintenance.vue') },
    { path: '/assets-mgmt/maintenance/new', name: 'NewAssetMaintenance', component: () => import('@/pages/assets/NewAssetMaintenance.vue') },
    { path: '/assets-mgmt/maintenance/:id', name: 'SavedAssetMaintenance', component: () => import('@/pages/assets/SavedAssetMaintenance.vue') },

    // Billing
    { path: '/billing', name: 'Billing', component: () => import('@/pages/billing/Billing.vue') },
    { path: '/billing/corporate', name: 'CorporateBillList', component: () => import('@/pages/billing/CorporateBillList.vue') },
    { path: '/billing/bill-transfers', name: 'BillTransferList', component: () => import('@/pages/billing/BillTransferList.vue') },

    // Rooms
    { path: '/rooms', name: 'RoomList', component: () => import('@/pages/rooms/RoomList.vue') },
    { path: '/rooms/new', name: 'NewRoom', component: () => import('@/pages/rooms/NewRoom.vue') },
    { path: '/rooms/:id', name: 'SavedRoom', component: () => import('@/pages/frontdesk/SavedRoom.vue') },

    // Others
    { path: '/reports', name: 'ReportList', component: () => import('@/pages/reports/ReportList.vue') },
    { path: '/reports/corporate-account-statement', name: 'CorporateAccountStatement', component: () => import('@/pages/reports/CorporateAccountStatement.vue') },
    { path: '/reports/daily-occupancy-report', name: 'DailyOccupancyReport', component: () => import('@/pages/reports/DailyOccupancyReport.vue') },
    { path: '/reports/guest-stay-history-report', name: 'GuestStayHistoryReport', component: () => import('@/pages/reports/GuestStayHistory.vue') },
    { path: '/reports/night-audit-summary-report', name: 'NightAuditSummaryReport', component: () => import('@/pages/reports/NightAuditSummaryReport.vue') },
    { path: '/reports/corporate-billing-statement', name: 'CorporateBillingStatementReport', component: () => import('@/pages/reports/CorporateBillingStatementReport.vue') },
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
    return { name: 'RoomView' }
  }

  return true
})

export default router