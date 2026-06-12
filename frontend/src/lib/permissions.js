/**
 * Centralized role-based access control configuration.
 *
 * Each entry maps a route-path prefix to an array of roles that are allowed
 * to access routes under that prefix.
 *
 * System Manager is implicitly allowed everywhere (handled in hasAnyRole).
 */

const ROLE_GROUPS = {
  frontDesk: ['Hotel Receptionist', 'Front Desk Manager', 'Hotel Manager'],
  rooms: ['Hotel Manager'],
  housekeeping: ['Housekeeping Supervisor', 'Front Desk Manager', 'Hotel Manager'],
  maintenance: ['Housekeeping Supervisor', 'Front Desk Manager', 'Hotel Manager'],
  billing: ['Front Desk Manager', 'Hotel Manager'],
  reports: ['Front Desk Manager', 'Hotel Manager'],
  pos: ['Sales User'],
  staffRoaster: ['Front Desk Manager', 'Hotel Manager'],
  kitchen: ['Kitchen User'],
  complimentary: ['Front Desk Manager', 'Hotel Manager'],
  assetManagement: ['Front Desk Manager', 'Hotel Manager'],
}

/**
 * Maps route path prefixes to role groups.
 * Order matters — more specific prefixes should come before less specific ones.
 */
export const ROUTE_PERMISSIONS = [
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

  { prefix: '/rooms', roles: ROLE_GROUPS.rooms },

  { prefix: '/housekeeping', roles: ROLE_GROUPS.housekeeping },

  { prefix: '/maintenance', roles: ROLE_GROUPS.maintenance },

  { prefix: '/billing', roles: ROLE_GROUPS.billing },

  { prefix: '/reports', roles: ROLE_GROUPS.reports },

  { prefix: '/pos/staff-roaster', roles: ROLE_GROUPS.staffRoaster },
  { prefix: '/pos/manager-dashboard', roles: ['Front Desk Manager', 'Hotel Manager'] },
  { prefix: '/pos', roles: ROLE_GROUPS.pos },

  { prefix: '/kitchen', roles: ROLE_GROUPS.kitchen },

  { prefix: '/complimentary', roles: ROLE_GROUPS.complimentary },

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
  if (userRoles.includes('System Manager')) {
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
