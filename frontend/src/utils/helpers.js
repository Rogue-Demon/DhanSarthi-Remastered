export const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

export const getInitials = (name = '') => {
  if (!name) return ''
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .substring(0, 2)
}

export const truncateText = (text = '', length = 50) => {
  if (!text) return ''
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

export const safeJsonParse = (str, fallback = null) => {
  try {
    return JSON.parse(str)
  } catch (e) {
    return fallback
  }
}

export const mapFrontendToBackendPersona = (persona) => {
  const mapping = {
    Student: 'STUDENT',
    'Working Professional': 'PROFESSIONAL',
    Business: 'BUSINESS',
  }
  return mapping[persona] || 'PROFESSIONAL'
}

export const mapBackendToFrontendPersona = (persona) => {
  const mapping = {
    STUDENT: 'Student',
    PROFESSIONAL: 'Working Professional',
    BUSINESS: 'Business',
  }
  return mapping[persona] || 'Working Professional'
}

export default {
  sleep,
  getInitials,
  truncateText,
  safeJsonParse,
  mapFrontendToBackendPersona,
  mapBackendToFrontendPersona,
}
