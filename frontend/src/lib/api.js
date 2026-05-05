function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]*)'))
  return match ? decodeURIComponent(match[2]) : ''
}

export function getCsrfToken() {
  return getCookie('csrf_token') || window.frappe?.csrf_token || ''
}

function parseServerMessages(serverMessages) {
  if (!serverMessages) return ''

  try {
    const parsed = typeof serverMessages === 'string' ? JSON.parse(serverMessages) : serverMessages
    if (!Array.isArray(parsed)) return ''

    const firstMessage = parsed[0]
    if (typeof firstMessage === 'string') {
      const nested = JSON.parse(firstMessage)
      return nested?.message || ''
    }

    return firstMessage?.message || ''
  } catch {
    return typeof serverMessages === 'string' ? serverMessages : ''
  }
}

function extractErrorMessage(payload, response) {
  const serverMessage = parseServerMessages(payload?._server_messages)
  const message = serverMessage || payload?.message || payload?.exc || response.statusText || 'Request failed'
  return typeof message === 'string' ? message : 'Request failed'
}

export async function requestApi(url, options = {}) {
  const config = { ...options }
  config.headers = { ...(options.headers || {}) }
  config.credentials = 'include'

  const method = String(config.method || 'GET').toUpperCase()
  const token = getCsrfToken()
  if (token && token !== 'Guest' && method !== 'GET') {
    config.headers['X-Frappe-CSRF-Token'] = token
  }

  if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData) && !(config.body instanceof URLSearchParams)) {
    config.headers['Content-Type'] = config.headers['Content-Type'] || 'application/json'
    config.body = JSON.stringify(config.body)
  }

  const response = await fetch(url, config)
  const raw = await response.text()

  let payload = {}
  if (raw) {
    try {
      payload = JSON.parse(raw)
    } catch {
      payload = { message: raw }
    }
  }

  if (!response.ok || payload?.exc) {
    throw new Error(extractErrorMessage(payload, response))
  }

  return payload
}

export async function callMethod(method, args = {}, options = {}) {
  const httpMethod = String(options.method || 'POST').toUpperCase()
  const payload = await requestApi(
    '/api/method/' + method,
    httpMethod === 'GET'
      ? { ...options, method: 'GET' }
      : { ...options, method: httpMethod, body: args }
  )

  return payload?.message
}

export async function callMethodForm(method, args = {}, options = {}) {
  const body = new URLSearchParams()
  for (const [key, value] of Object.entries(args || {})) {
    if (value !== '' && value !== null && value !== undefined) {
      body.append(key, String(value))
    }
  }

  const payload = await requestApi('/api/method/' + method, {
    method: String(options.method || 'POST').toUpperCase(),
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      ...(options.headers || {}),
    },
    body,
    ...options,
  })

  return payload?.message
}
