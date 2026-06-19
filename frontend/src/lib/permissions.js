/**
 * Centralized role-based access control configuration.
 *
 * Each entry maps a route-path prefix to an array of roles that are allowed
 * to access routes under that prefix.
 *
 * System Manager and Hotel Manager are implicitly allowed everywhere (handled in hasAnyRole).
 */

const ROLE_GROUPS = {
  // Front Desk module
  frontDesk: ['Hotel Receptionist', 'Front Desk Manager'],

  // Rooms management
  rooms: ['Front Desk Manager'],

  // Housekeeping - task list only (staff level)
  housekeepingList: ['House keeper', 'Housekeeping Manager'],
  // Housekeeping - full module (dashboard, report, assign)
  housekeepingFull: ['Housekeeping Manager'],

  // Maintenance - list only (staff level)
  maintenanceList: ['Technician', 'Maintenance Manager','Employee','Facility Manager'],
  // Maintenance - front desk access (request view only)
  maintenanceFrontDesk: ['Hotel Receptionist', 'Front Desk Manager', 'Technician', 'Maintenance Manager'],
  // Maintenance - full module (dashboard, requests, technicians)
  maintenanceFull: ['Maintenance Manager'],

  // Billing
  billing: ['Hotel Receptionist', 'Front Desk Manager'],

  // Reports - front desk related
  reportsFrontDesk: ['Hotel Receptionist', 'Front Desk Manager'],
  // Reports - POS related (manager only)
  reportsPos: ['Sales Manager'],
  // Reports - housekeeping related
  reportsHousekeeping: ['Housekeeping Manager'],

  // POS - basic (dashboard only)
  posBasic: ['Sales User', 'Sales Manager'],
  // POS - full module (manager dashboard, invoices, shift logs)
  posManager: ['Sales Manager'],

  // Staff Roaster - view published only (all staff)
  staffRoasterView: [
    'Hotel Receptionist', 'Front Desk Manager',
    'Sales User', 'Sales Manager',
    'House keeper', 'Housekeeping Manager',
    'Technician', 'Maintenance Manager',
    'Kitchen Staff', 'Employee',
  ],
  // Staff Roaster - full module (managers only, filtered to department)
  staffRoasterFull: [
    'Front Desk Manager',
    'Sales Manager',
    'Housekeeping Manager',
    'Maintenance Manager',
  ],

  // Kitchen Terminal - view access
  kitchen: ['Sales User', 'Sales Manager', 'Kitchen Staff'],
  // Kitchen Terminal - can update ticket status (kitchen staff only, not POS users)
  kitchenActions: ['Kitchen Staff'],

  // Complimentary management (managers only)
  complimentary: ['Front Desk Manager', 'Sales Manager'],
  complimentaryCreate: ['Front Desk Manager', 'Sales Manager'],

  // Asset Management
  assetManagement: ['Maintenance Manager'],
}

/**
 * Maps route path prefixes to role groups.
 * Order matters — more specific prefixes should come before less specific ones.
 */
export const ROUTE_PERMISSIONS = [
  // Front Desk
  { prefix: '/room-view', roles: ROLE_GROUPS.frontDesk },
  { prefix: '/available-rooms', roles: ROLE_GROUPS.frontDesk },
  { prefix: '/check-ins', roles: ROLE_GROUPS.frontDesk },
  { prefix: '/check-outs', roles: ROLE_GROUPS.frontDesk },
  { prefix: '/reservations', roles: ROLE_GROUPS.frontDesk },
  { prefix: '/payments', roles: ROLE_GROUPS.frontDesk },
  { prefix: '/guests', roles: ROLE_GROUPS.frontDesk },
  { prefix: '/night-audit', roles: ROLE_GROUPS.frontDesk },
  { prefix: '/hall-dashboard', roles: ROLE_GROUPS.frontDesk },
  { prefix: '/hall', roles: ROLE_GROUPS.frontDesk },

  // Staff Roaster / Shift — manager pages
  { prefix: '/weekly-shift-generator', roles: ROLE_GROUPS.staffRoasterFull },
  { prefix: '/shift-list', roles: ROLE_GROUPS.staffRoasterView },
  { prefix: '/shift-preference-manager', roles: ROLE_GROUPS.staffRoasterFull },
  { prefix: '/staff-roaster-dashboard', roles: ROLE_GROUPS.staffRoasterFull },
  // Staff Roaster / Shift — all staff pages
  { prefix: '/swap-requests', roles: ROLE_GROUPS.staffRoasterView },
  { prefix: '/shift-preference', roles: ROLE_GROUPS.staffRoasterView },

  // Rooms
  { prefix: '/rooms', roles: ROLE_GROUPS.rooms },

  // Housekeeping — specific paths before general
  { prefix: '/housekeeping/dashboard', roles: ROLE_GROUPS.housekeepingFull },
  { prefix: '/housekeeping/report', roles: ROLE_GROUPS.housekeepingFull },
  { prefix: '/housekeeping/task/new', roles: [...ROLE_GROUPS.housekeepingList, ...ROLE_GROUPS.frontDesk] },
  { prefix: '/housekeeping/task', roles: [...ROLE_GROUPS.housekeepingList, 'Front Desk Manager'] },
  { prefix: '/housekeeping', roles: [...ROLE_GROUPS.housekeepingList, ...ROLE_GROUPS.frontDesk] },

  // Maintenance — specific paths before general
  { prefix: '/maintenance/dashboard', roles: ROLE_GROUPS.maintenanceFull },
  { prefix: '/maintenance/request', roles: [...ROLE_GROUPS.maintenanceFull, ...ROLE_GROUPS.frontDesk] },
  { prefix: '/maintenance/new-request', roles: [...ROLE_GROUPS.maintenanceFull, ...ROLE_GROUPS.frontDesk] },
  { prefix: '/maintenance/technicians', roles: ROLE_GROUPS.maintenanceFull },
  { prefix: '/maintenance/new-technician', roles: ROLE_GROUPS.maintenanceFull },
  { prefix: '/maintenance/new-task', roles: ROLE_GROUPS.maintenanceFull },
  { prefix: '/maintenance/list', roles: ROLE_GROUPS.maintenanceList },
  { prefix: '/maintenance/task', roles: ROLE_GROUPS.maintenanceList },

  // Billing — specific paths before general
  { prefix: '/billing/reconcile', roles: ['Front Desk Manager'] },
  { prefix: '/billing', roles: ROLE_GROUPS.billing },

  // Reports — individual report routes
  { prefix: '/reports/daily-occupancy-report', roles: ROLE_GROUPS.reportsFrontDesk },
  { prefix: '/reports/night-audit-summary-report', roles: ROLE_GROUPS.reportsFrontDesk },
  { prefix: '/reports/corporate-account-statement', roles: ROLE_GROUPS.reportsFrontDesk },
  { prefix: '/reports/corporate-billing-statement', roles: ROLE_GROUPS.reportsFrontDesk },
  { prefix: '/reports/complimentary-house-use-report', roles: ROLE_GROUPS.reportsFrontDesk },
  { prefix: '/reports/guest-stay-history-report', roles: ROLE_GROUPS.reportsFrontDesk },
  { prefix: '/reports/pos-sales-report', roles: ROLE_GROUPS.reportsPos },
  { prefix: '/reports/house-keeping-productivity-report', roles: ROLE_GROUPS.reportsHousekeeping },
  // Report list page — anyone with access to any report
  { prefix: '/reports', roles: [...ROLE_GROUPS.reportsFrontDesk, ...ROLE_GROUPS.reportsPos, ...ROLE_GROUPS.reportsHousekeeping] },

  // POS — specific paths before general
  { prefix: '/pos/staff-roaster', roles: ROLE_GROUPS.staffRoasterFull },
  { prefix: '/pos/manager-dashboard', roles: ROLE_GROUPS.posManager },
  { prefix: '/pos/invoices', roles: ROLE_GROUPS.posManager },
  { prefix: '/pos/shift-difference-log', roles: ROLE_GROUPS.posManager },
  { prefix: '/pos/shift-close', roles: ROLE_GROUPS.posManager },
  { prefix: '/pos', roles: ROLE_GROUPS.posBasic },

  // Kitchen
  { prefix: '/kitchen', roles: ROLE_GROUPS.kitchen },

  // Complimentary
  { prefix: '/complimentary/new', roles: ROLE_GROUPS.complimentaryCreate },
  { prefix: '/complimentary', roles: ROLE_GROUPS.complimentary },

  // Asset Management
  { prefix: '/assets-mgmt', roles: ROLE_GROUPS.assetManagement },
]

/**
 * Returns the required roles for a given route path, or null if unrestricted.
 */
export function getRequiredRoles(path) {
  for (const entry of ROUTE_PERMISSIONS) {
    if (path === entry.prefix || path.startsWith(entry.prefix + '/')) {
      return entry.roles
    }
  }
  return null
}

/**
 * Returns the first allowed route path for a user given their roles.
 * Used as a fallback redirect when the user cannot access their target route.
 */
export function getFirstAllowedRoute(userRoles) {
  if (userRoles.includes('System Manager') || userRoles.includes('Hotel Manager')) {
    return '/room-view'
  }

  for (const entry of ROUTE_PERMISSIONS) {
    if (entry.roles.some((role) => userRoles.includes(role))) {
      return entry.prefix
    }
  }

  return '/login'
}

export { ROLE_GROUPS }
