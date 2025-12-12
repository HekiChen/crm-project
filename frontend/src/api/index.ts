/**
 * Axios instance configuration with interceptors
 */

import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { getToken, getRefreshToken, setToken, clearTokens } from '@/utils/token'
import type { ApiError } from '@/types'

// Create axios instance
const instance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Flag to track if token refresh is in progress
let isRefreshing = false
// Queue to store failed requests during token refresh
let failedQueue: Array<{
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}> = []

/**
 * Process all queued requests after token refresh
 */
const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Request interceptor - add auth token
instance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  },
)

// Response interceptor - unwrap response and handle errors
instance.interceptors.response.use(
  (response) => {
    // Backend wraps all responses in {data: {...}, meta: {...}}
    // Unwrap to return just the inner data for cleaner API
    if (response.data && typeof response.data === 'object' && 'data' in response.data) {
      response.data = response.data.data
    }
    return response
  },
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response) {
      const { status, data } = error.response

      // Handle 401 Unauthorized
      if (status === 401 && originalRequest && !originalRequest._retry) {
        // Don't retry if this is already a refresh token request or login
        if (originalRequest.url?.includes('/auth/refresh') || originalRequest.url?.includes('/auth/login')) {
          clearTokens()
          window.location.href = '/login'
          return Promise.reject(new Error('Session expired - please login again'))
        }

        // If token refresh is already in progress, queue this request
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject })
          })
            .then(() => {
              // Retry the request with new token
              const token = getToken()
              if (token && originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`
              }
              return instance(originalRequest)
            })
            .catch((err) => {
              return Promise.reject(err)
            })
        }

        // Mark request as retried to prevent infinite loops
        originalRequest._retry = true
        isRefreshing = true

        const refreshToken = getRefreshToken()
        if (!refreshToken) {
          // No refresh token available, redirect to login
          isRefreshing = false
          clearTokens()
          window.location.href = '/login'
          return Promise.reject(new Error('No refresh token - please login again'))
        }

        try {
          // Attempt to refresh the token
          const response = await axios.post(
            `${instance.defaults.baseURL}/auth/refresh`,
            { refresh_token: refreshToken },
            {
              headers: {
                'Content-Type': 'application/json',
              },
            }
          )

          // Extract new access token
          const newAccessToken = response.data?.data?.access_token || response.data?.access_token

          if (!newAccessToken) {
            throw new Error('No access token in refresh response')
          }

          // Update stored token
          setToken(newAccessToken)

          // Update authorization header for the original request
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          }

          // Process queued requests
          processQueue(null, newAccessToken)

          // Retry the original request
          isRefreshing = false
          return instance(originalRequest)
        } catch (refreshError) {
          // Token refresh failed - clear tokens and redirect to login
          processQueue(refreshError as Error, null)
          isRefreshing = false
          clearTokens()
          window.location.href = '/login'
          return Promise.reject(new Error('Session expired - please login again'))
        }
      }

      // Handle other errors
      const errorMessage = data?.message || error.message || 'An error occurred'
      return Promise.reject(new Error(errorMessage))
    }

    // Network error or request timeout
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new Error('Request timeout'))
    }

    return Promise.reject(new Error('Network error - please check your connection'))
  },
)

export default instance
