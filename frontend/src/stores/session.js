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
      const data = await callMethod('frappe.client.get', {
        doctype: 'User',
        name: user.value,
      })
      fullName.value = data?.full_name || user.value
      roles.value = Array.isArray(data?.roles) ? data.roles.map((r) => r.role) : []
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
    initialized.value = true

    try {
      await callMethod('logout', {}, { method: 'GET' })
    } catch {
      // Ignore logout errors and continue redirecting to login.
    }

    window.location.href = '/frontdesk/login'
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
    initialize,
    logout,
  }
})