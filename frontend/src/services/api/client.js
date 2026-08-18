import { envConfig } from '@/config'
import { requestInterceptor, responseInterceptor } from './interceptors'

export class ApiError extends Error {
  constructor(message, status, detail = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export const apiClient = {
  request: async (url, options = {}) => {
    const fullUrl = `${envConfig.apiBaseUrl}${url}`
    const interceptedOptions = requestInterceptor(options)

    try {
      const response = await fetch(fullUrl, interceptedOptions)
      const processedResponse = await responseInterceptor(response)

      if (!processedResponse.ok) {
        let errorDetail = null
        let errorMessage = `HTTP error! status: ${processedResponse.status}`
        try {
          const errJson = await processedResponse.json()
          errorDetail = errJson.detail || errJson.message || null
          if (errorDetail) {
            if (typeof errorDetail === 'string') {
              errorMessage = errorDetail
            } else if (Array.isArray(errorDetail)) {
              errorMessage = errorDetail
                .map((err) => {
                  const field = err.loc ? err.loc.join('.') : 'field'
                  return `${field}: ${err.msg}`
                })
                .join(', ')
            } else if (typeof errorDetail === 'object') {
              errorMessage = errorDetail.message || JSON.stringify(errorDetail)
            }
          }
        } catch {
          // Response is not JSON
        }
        throw new ApiError(errorMessage, processedResponse.status, errorDetail)
      }

      if (processedResponse.status === 204) {
        return null
      }

      const text = await processedResponse.text()
      return text ? JSON.parse(text) : null
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      console.error(`API Request to ${url} failed:`, error)
      throw error
    }
  },
  get: (url, options = {}) => apiClient.request(url, { ...options, method: 'GET' }),
  patch: (url, data, options = {}) => {
    const isFormData = data instanceof FormData
    return apiClient.request(url, {
      ...options,
      method: 'PATCH',
      body: isFormData ? data : data !== undefined ? JSON.stringify(data) : undefined,
    })
  },
  post: (url, data, options = {}) => {
    const isFormData = data instanceof FormData
    return apiClient.request(url, {
      ...options,
      method: 'POST',
      body: isFormData ? data : data !== undefined ? JSON.stringify(data) : undefined,
    })
  },
  put: (url, data, options = {}) => {
    const isFormData = data instanceof FormData
    return apiClient.request(url, {
      ...options,
      method: 'PUT',
      body: isFormData ? data : data !== undefined ? JSON.stringify(data) : undefined,
    })
  },
  delete: (url, options = {}) => apiClient.request(url, { ...options, method: 'DELETE' }),
}

export default apiClient
