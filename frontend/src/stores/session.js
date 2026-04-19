import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'

export const useSessionStore = defineStore('session', () => {
  function getSessionUser() {
    const cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
    const user = cookies.get('user_id')
    return user === 'Guest' ? null : user
  }

  function logout() {
    user.value = null
    fullName.value = ''
    roles.value = []

    // Also call Frappe logout to clear the session cookie
    fetch('/api/method/logout', {
      method: 'GET',
      credentials: 'include',
    }).finally(() => {
      window.location.href = '/front-desk/login'
    })
  }


  const user = ref(getSessionUser())
  const fullName = ref('')
  const roles = ref([])
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

  // Fetch full name and roles from Frappe
  const userResource = createResource({
    url: 'frappe.client.get',
    params: {
      doctype: 'User',
      name: user.value,
      fieldname: ['full_name', 'roles'],
    },
    auto: !!user.value,
    onSuccess(data) {
      fullName.value = data.full_name || user.value
      roles.value = data.roles?.map(r => r.role) || []
    },
  })

  // Display name — full name if available, otherwise username before @
  const displayName = computed(() => {
    if (fullName.value) return fullName.value
    if (user.value?.includes('@')) return user.value.split('@')[0]
    return user.value || ''
  })

  return {
    user,
    fullName,
    roles,
    isLoggedIn,
    displayName,
    isSystemManager,
    isHotelManager,
    isFrontDeskManager,
    isReceptionist,
    logout,
  }
})