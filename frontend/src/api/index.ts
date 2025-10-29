/**
 * Axios instance configuration with interceptors
 */

import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { getToken, clearTokens } from '@/utils/token'
import type { ApiError } from '@/types'

// Create axios instance
const instance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
    if (error.response) {
      const { status, data } = error.response

      // Handle 401 Unauthorized
      if (status === 401) {
        // Clear tokens and redirect to login
        clearTokens()
        // Redirect to login page
        window.location.href = '/login'
        return Promise.reject(new Error('Unauthorized - please login again'))
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
