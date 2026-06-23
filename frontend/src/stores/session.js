// import { defineStore } from 'pinia'
// import { ref, computed } from 'vue'
// import { callMethod } from '@/lib/api'

// export const useSessionStore = defineStore('session', () => {
//   const user = ref(null)
//   const fullName = ref('')
//   const roles = ref([])
//   const initialized = ref(false)

//   let initializePromise = null

//   function clearProfile() {
//     fullName.value = ''
//     roles.value = []
//   }

//   async function loadUserProfile() {
//     if (!user.value) {
//       clearProfile()
//       return
//     }

//     try {
//       const data = await callMethod('rhohotel.api.get_current_user_info')
//       fullName.value = data?.full_name || user.value
//       roles.value = Array.isArray(data?.roles) ? data.roles : []
//     } catch {
//       clearProfile()
//     }
//   }

//   async function initialize(force = false) {
//     if (initialized.value && !force) return
//     if (initializePromise) return initializePromise

//     initializePromise = (async () => {
//       try {
//         const loggedUser = await callMethod('frappe.auth.get_logged_user', {}, { method: 'GET' })
//         user.value = loggedUser && loggedUser !== 'Guest' ? loggedUser : null
//         await loadUserProfile()
//       } catch {
//         user.value = null
//         clearProfile()
//       } finally {
//         initialized.value = true
//         initializePromise = null
//       }
//     })()

//     return initializePromise
//   }

//   async function logout() {
//     user.value = null
//     clearProfile()
//     initialized.value = true

//     try {
//       await callMethod('logout', {}, { method: 'GET' })
//     } catch {
//       // Ignore logout errors and continue redirecting to login.
//     }

//     window.location.href = '/frontdesk/login'
//   }

//   const isLoggedIn = computed(() => !!user.value)

//   const isSystemManager = computed(() => roles.value.includes('System Manager'))
//   const isHotelManager = computed(() =>
//     roles.value.includes('Hotel Manager') || isSystemManager.value
//   )
//   const isFrontDeskManager = computed(() =>
//     roles.value.includes('Front Desk Manager') || isHotelManager.value
//   )
//   const isReceptionist = computed(() =>
//     roles.value.includes('Hotel Receptionist') || isFrontDeskManager.value
//   )

//   const displayName = computed(() => {
//     if (fullName.value) return fullName.value
//     if (user.value?.includes('@')) return user.value.split('@')[0]
//     return user.value || ''
//   })

//   /**
//    * Returns true if the user has any of the provided roles,
//    * or if the user is a System Manager / Hotel Manager (universal access).
//    */
//   function hasAnyRole(requiredRoles) {
//     if (!requiredRoles || requiredRoles.length === 0) return true
//     if (roles.value.includes('System Manager')) return true
//     if (roles.value.includes('Hotel Manager')) return true
//     return requiredRoles.some((role) => roles.value.includes(role))
//   }

//   return {
//     user,
//     fullName,
//     roles,
//     initialized,
//     isLoggedIn,
//     displayName,
//     isSystemManager,
//     isHotelManager,
//     isFrontDeskManager,
//     isReceptionist,
//     hasAnyRole,
//     initialize,
//     logout,
//   }
// })


import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { callMethod } from '@/lib/api'

export const useSessionStore = defineStore('session', () => {
  const user = ref(null)
  const fullName = ref('')
  const roles = ref([])
  const initialized = ref(false)

  let initializePromise = null

  function clearProfile() {
    fullName.value = ''
    roles.value = []
  }

  async function loadUserProfile() {
    if (!user.value) {
      clearProfile()
      return
    }

    try {
      const data = await callMethod('rhohotel.api.get_current_user_info', {}, { method: 'GET' })
      fullName.value = data?.full_name || user.value
      roles.value = Array.isArray(data?.roles) ? data.roles : []
    } catch {
      clearProfile()
    }
  }

  async function initialize(force = false) {
    if (initialized.value && !force) return
    if (initializePromise) return initializePromise

    initializePromise = (async () => {
      try {
        const loggedUser = await callMethod('frappe.auth.get_logged_user', {}, { method: 'GET' })
        user.value = loggedUser && loggedUser !== 'Guest' ? loggedUser : null
        await loadUserProfile()
      } catch {
        user.value = null
        clearProfile()
      } finally {
        initialized.value = true
        initializePromise = null
      }
    })()

    return initializePromise
  }

  async function logout() {
    user.value = null
    clearProfile()
    initialized.value = false

    try {
      await callMethod('logout', {}, { method: 'GET' })
    } catch {}

    window.location.href = '/login'
  }

  const isLoggedIn = computed(() => !!user.value)

  const isSystemManager = computed(() => roles.value.includes('System Manager'))
  const isHotelManager = computed(() =>
    roles.value.includes('Hotel Manager') || isSystemManager.value
  )
  const isFrontDeskManager = computed(() =>
    roles.value.includes('Front Desk Manager') || isHotelManager.value
  )
  const isReceptionist = computed(() =>
    roles.value.includes('Hotel Receptionist') || isFrontDeskManager.value
  )

  const displayName = computed(() => {
    if (fullName.value) return fullName.value
    if (user.value?.includes('@')) return user.value.split('@')[0]
    return user.value || ''
  })

  function hasAnyRole(requiredRoles) {
    if (!requiredRoles || requiredRoles.length === 0) return true
    if (roles.value.includes('System Manager')) return true
    if (roles.value.includes('Hotel Manager')) return true
    return requiredRoles.some((role) => roles.value.includes(role))
  }

  return {
    user,
    fullName,
    roles,
    initialized,
    isLoggedIn,
    displayName,
    isSystemManager,
    isHotelManager,
    isFrontDeskManager,
    isReceptionist,
    hasAnyRole,
    initialize,
    logout,
  }
})