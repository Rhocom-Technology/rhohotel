<template>
  <header class="h-14 flex-shrink-0 flex items-center justify-between px-6 border-b border-white/10" style="background-color: #1a1f2e;">
    <div>
      <h1 class="text-white font-bold text-lg leading-tight">{{ pageTitle }}</h1>
      <p class="text-gray-400 text-xs">{{ pageSubtitle }}</p>
    </div>
    <div class="flex items-center gap-3">
      <div class="text-white text-sm font-medium italic">
        {{ greeting }}, {{ session.displayName }}
      </div>
      <div class="bg-blue-600 text-white text-xs font-medium px-3 py-1.5 rounded-full">
        {{ currentDateTime }}
      </div>
      <button @click="logout" class="text-gray-400 hover:text-white text-xs transition-colors ml-2">
        Logout
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSessionStore } from '@/stores/session'

const route = useRoute()
const session = useSessionStore()
const now = ref(new Date())

let timer
onMounted(() => { timer = setInterval(() => { now.value = new Date() }, 1000) })
onUnmounted(() => clearInterval(timer))

const pageMeta = {
  // Front Desk
  'RoomView':             { title: 'Front Desk Command Center', subtitle: 'Real-time room operations, overdue checkout watch, guest occupancy visibility' },
  'CheckIns':             { title: 'Check-in List', subtitle: 'Front desk • all guest check-in history and active stays' },
  'CheckInDetail': { title: 'Check-in Detail', subtitle: 'Front desk • guest stay details, billing, and departure actions' },
  'NewCheckIn': { title: 'New Check-In', subtitle: 'Professional front desk check-in flow' },
  'CheckOuts':            { title: 'Check-out List', subtitle: 'Front desk • checked-out guest records' },
  'CheckOutOverdue': { title: 'Check-out Overdue', subtitle: 'Front desk • overdue departure monitoring' },
  'Reservations':         { title: 'Reservations', subtitle: 'Reservation section • list view' },
  'NewReservation':       { title: 'New Reservation', subtitle: 'Individual and corporate reservations with guest selection, stay dates, room choice, rate auto-fill, discount control, and grand total' },
  'SavedReservation':     { title: 'Reservation', subtitle: 'Saved reservation record with payment, adjustment, room change, cancellation, and check-in actions' },
  'GuestList':            { title: 'Guest List', subtitle: 'Guest section • list view' },
  'Payments':             { title: 'Payments', subtitle: 'Front desk billing • payment list' },
  'NightAudit':           { title: 'Night Audit', subtitle: 'End of day audit and reconciliation' },
  'GuestProfile': { title: 'Guest Profile Intelligence', subtitle: '360-degree guest record with stay history, spend, loyalty, risk, messages, preferences, and current stay snapshot' },
'EditGuest':    { title: 'Edit Existing Guest',        subtitle: 'Guest profile • update guest identity, contact details, preferences, and supporting documents' },
'NewGuest':     { title: 'New Guest',                  subtitle: 'Guest profile • create a new guest identity, contact details, preferences, and supporting documents' },

  // Housekeeping
  'Housekeeping':             { title: 'Housekeeping', subtitle: 'Housekeeping section • task list view' },
  'HousekeepingDashboard':    { title: 'Housekeeping Dashboard', subtitle: 'Room operations • cleaning status • team workload' },
  'HousekeepingTask':         { title: 'Housekeeping Task', subtitle: 'Task detail • room assignment, cleaning checklist, inventory updates, and status control' },
  'NewHousekeepingTask':      { title: 'Housekeeping Task', subtitle: 'Task detail • room assignment, cleaning checklist, inventory updates, and status control' },
  'HousekeepingReport':               { title: 'Housekeeping Report', subtitle: 'Housekeeping operations and stay analytics' },

  // Maintenance
  'MaintenanceList':          { title: 'Maintenance List', subtitle: 'Operations • full maintenance register for preventive and corrective tasks' },
  'MaintenanceDashboard':     { title: 'Maintenance Dashboard', subtitle: 'Monitor tasks, technician load, and maintenance performance' },
  'MaintenanceRequest':       { title: 'Maintenance Request List', subtitle: 'Operations • track staff-submitted maintenance requests for room, location, or asset issues' },
  'NewMaintenanceRequest':    { title: 'Maintenance Request', subtitle: 'Staff request • report an issue on a location, room, or asset for maintenance action' },
  'SavedMaintenanceRequest':  { title: 'Saved Maintenance Request', subtitle: 'Operations • saved request details with routing and task conversion control' },
  'MaintenanceTask':          { title: 'Maintenance Task', subtitle: 'Task detail • asset issue, technician assignment, parts used, checklist, and status update' },
  'NewMaintenanceTask':       { title: 'New Maintenance Task', subtitle: 'Create task • asset issue, assignment, parts planning, and maintenance workflow setup' },
  'TechnicianList':           { title: 'Technician List', subtitle: 'Operations • in-house employees and outsourced technicians for maintenance assignments' },
  'TechnicianView':           { title: 'Technician View', subtitle: 'Operations • technician profile, source type, skills, assignments, and performance summary' },
  'NewTechnician':            { title: 'New Technician', subtitle: 'Create technician • in-house employee or outsourced service provider setup' },

  // POS
  'PointOfSales':         { title: 'Point of Sales', subtitle: 'POS dashboard and transaction management' },
  'POSShiftClose': { title: 'POS / Shift Closing', subtitle: 'Point of sale • end-of-shift reconciliation and terminal closing' },
  'POSInvoiceList': { title: 'POS Invoice List', subtitle: 'Point of sale • invoice history and billing records' },
  'POSManagerDashboard': { title: 'POS Manager Dashboard', subtitle: 'Point of sale • multi-terminal oversight and performance analytics' },
'POSShiftDifferenceLog': { title: 'Shift Difference Log', subtitle: 'Point of sale • difference history, reviews and resolutions' },
'StaffRoasterPage': { title: 'View Staff Roaster', subtitle: 'Point of sale • cashier and outlet staff scheduling overview' },

  // Kitchen
  'KitchenTerminal': { title: 'Kitchen Terminal Dashboard', subtitle: 'Point of sale • kitchen display and order preparation control' },

  // Complimentary
  'Complimentary': { title: 'Complimentary', subtitle: 'Complimentary service tracking and management' },
  'ComplimentaryList': { title: 'Complimentary List', subtitle: 'Complimentary service tracking and management' },
  'NewComplimentary': { title: 'New Complimentary', subtitle: 'Complimentary service tracking and management' },
  'SavedComplimentary': { title: 'Saved Complimentary', subtitle: 'Complimentary service tracking and management' },


  'CheckOut': { title: 'Check-out', subtitle: 'Front desk • check-out and final billing workflow' },
  'SavedRoom': { title: 'Saved Room', subtitle: 'Operations • room configuration and current status display' },

    // Asset Management
  'AssetManagement': { title: 'Asset Management Dashboard', subtitle: 'Operations • asset inventory, maintenance, lifecycle, and utilization monitoring' },
  'AssetList':       { title: 'Asset List',                  subtitle: 'Operations • central asset register for rooms, facilities, and equipment' },

  // Billing
  'Billing':          { title: 'Billing Dashboard',    subtitle: 'Billing • individual and corporate account monitoring with invoice and payment controls' },
  'CorporateBillList':{ title: 'Corporate Bills List',  subtitle: 'Corporate billing • company bills, statements, outstanding balances, and payment follow-up' },


  // Others
  'ReportList': { title: 'Report List', subtitle: 'Central report library for hotel operations, billing, housekeeping, POS, and management analysis' },
  'DailyOccupancyReport': { title: 'Daily Occupancy Report', subtitle: 'Hotel performance and occupancy overview' },
  'GuestStayHistoryReport': { title: 'Guest Stay History Report', subtitle: 'Hotel performance and occupancy overview' },
  'NightAuditSummaryReport': { title: 'Night Audit Summary Report', subtitle: 'Operations, finance, and control overview for end-of-day review' },
  'CorporateAccountStatement':              { title: 'Corporate Account Statement', subtitle: 'Hotel performance and occupancy overview' },
  'CorporateBillingStatementReport':              { title: 'Corporate Billing Statement', subtitle: 'Corporate account ledger with running balance, payments, outstanding exposure, and date filter controls' },
  'PosSalesReport':              { title: 'POS Sales Report', subtitle: 'Point of Sales performance and sales overview' },
  'HouseKeepingProductivityReport':              { title: 'Housekeeping Productivity Report', subtitle: 'Housekeeping performance and productivity overview' },
}

const pageTitle = computed(() => pageMeta[route.name]?.title || 'Dashboard')
const pageSubtitle = computed(() => pageMeta[route.name]?.subtitle || '')

const greeting = computed(() => {
  const hour = now.value.getHours()
  if (hour < 12) return 'Good Morning'
  if (hour < 17) return 'Good Afternoon'
  return 'Good Evening'
})

const currentDateTime = computed(() => {
  return now.value.toLocaleString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
})

function logout() {
  session.logout()
}
</script>