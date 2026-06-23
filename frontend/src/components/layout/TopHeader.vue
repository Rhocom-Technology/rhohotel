<template>
  <header class="min-h-14 flex-shrink-0 flex items-center justify-between gap-3 px-3 py-2 sm:px-4 lg:px-6 border-b border-white/10" style="background-color: #1a1f2e;">
    <div class="flex min-w-0 items-center gap-3">
      <button
        type="button"
        class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-gray-300 hover:bg-white/10 hover:text-white md:hidden"
        aria-label="Open navigation menu"
        @click="openSidebar"
      >
        <Menu class="h-5 w-5" />
      </button>
      <div class="min-w-0">
        <h1 class="truncate text-white font-bold text-base leading-tight sm:text-lg">{{ pageTitle }}</h1>
        <p class="hidden truncate text-gray-400 text-xs sm:block">{{ pageSubtitle }}</p>
      </div>
    </div>
    <div class="flex flex-shrink-0 items-center gap-2 sm:gap-3">
      <div class="hidden text-white text-sm font-medium italic lg:block">
        {{ greeting }}, {{ session.displayName }}
      </div>
      <div class="hidden bg-blue-600 text-white text-xs font-medium px-3 py-1.5 rounded-full xl:block">
        {{ currentDateTime }}
      </div>
      <button @click="logout" class="text-gray-300 hover:text-white text-xs transition-colors sm:ml-1">
        Logout
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { Menu } from 'lucide-vue-next'

const emit = defineEmits(['open-sidebar'])

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

  //Shifts
  'WeeklyShiftGenerator': { title: 'Weekly Shift Generator', subtitle: 'Department supervisor tool • manually assign or AI auto-assign weekly shifts for all staff in selected department' },
  'ShiftList': { title: 'Shift List', subtitle: 'HRMS • published staff shifts by specific date, including morning, afternoon, and night shifts' },
  'SwapRequestList': { title: 'Swap Request List', subtitle: 'HRMS • staff shift swap requests, manager review, approval, rejection, and conflict control' },
  'StaffShiftPreference': { title: 'Staff Shift Preference', subtitle: 'Self-service • current staff can submit preferred weekly shifts for manager guidance' },
  'StaffRoasterDashboard': { title: 'Staff Roaster Dashboard', subtitle: 'HRMS • weekly planning, AI auto-assignment, staff preferences, published shifts, swaps, and attendance readiness' },
  'StaffShiftPreferenceManagerView': { title: 'Staff Shift Preference - Manager View', subtitle: 'Manager view • review staff weekly preferences and use them to guide manual or AI shift generation' },

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

  
  // Hall Management
  'HallBookingList': { title: 'Hall Bookings',    subtitle: 'Front desk • all hall bookings, payment status, and booking management' },
  'HallDashboard': { title: 'Hall Dashboard',    subtitle: 'Monitor hall reservation performance from one screen' },
  'NewHallBooking':  { title: 'New Hall Booking', subtitle: 'Front desk • create a new hall booking and generate invoice' },
  'HallBooking':     { title: 'Hall Booking',     subtitle: 'Front desk • booking details, payment, and adjustment' },
  'HallList':  { title: 'Hall List',  subtitle: 'Front desk • view all halls, monitor availability, and manage hall setup, rates, and operational status' },
  'NewHall':   { title: 'New Hall',   subtitle: 'Front desk • create and configure a new hall or banquet space' },
  'EditHall':  { title: 'Edit Hall',  subtitle: 'Front desk • update hall profile, facilities, pricing, and configuration' },
  'SavedHall': { title: 'Saved Hall', subtitle: 'Front desk • hall profile, facilities, rates, bookings, and operating status' },


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
  'ComplimentaryHouseUseReport':              { title: 'Complimentary & House Use Report', subtitle: 'Internal stays, authorisation, room nights, and theoretical revenue' },
  'PosSalesReport':              { title: 'POS Sales Report', subtitle: 'Point of Sales performance and sales overview' },
  'KitchenOrderReport':              { title: 'Kitchen Order Report', subtitle: 'Kitchen ticket volume, preparation flow, delays, and completion analytics' },
  'GuestLedgerReport':              { title: 'Guest Ledger Report', subtitle: 'Guest folio balances, collections, and settlement status by check-in' },
  'HousekeepingProductivityReport':              { title: 'Housekeeping Productivity Report', subtitle: 'Housekeeping performance and productivity overview' },
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

function openSidebar() {
  emit('open-sidebar')
}

function logout() {
  session.logout()
}
</script>
