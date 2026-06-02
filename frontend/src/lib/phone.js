export function compactPhone(value) {
  return String(value || '').trim().replace(/[\s().-]/g, '')
}

export function isValidPhone(value, { required = false } = {}) {
  const raw = String(value || '').trim()
  if (!raw) return !required
  const compact = compactPhone(raw)
  const digits = compact.replace(/\D/g, '')
  return /^\+?\d+$/.test(compact) && digits.length >= 7 && digits.length <= 15
}

export function buildPhoneWithCountry(countryCode, phoneNumber) {
  const phone = String(phoneNumber || '').trim()
  if (!phone) return ''
  if (phone.startsWith('+')) return phone
  return `${countryCode || ''}${phone}`
}

export function phoneError(label = 'Phone number') {
  return `${label} must be a valid number with 7 to 15 digits.`
}
