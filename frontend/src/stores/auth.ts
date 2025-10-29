/**
 * Authentication Store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { getToken, setToken, getRefreshToken, setRefreshToken, clearTokens } from '@/utils/token'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(getToken())
  const refreshToken = ref<string | null>(getRefreshToken())

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userInfo = computed(() => user.value)

  // Actions

  /**
   * Login action - will be implemented when backend auth endpoints are ready
   * @param username - User's username
   * @param password - User's password
   */
  async function login(username: string, password: string): Promise<void> {
    // TODO: Implement when backend /api/v1/auth/login is available
    // For now, this is a placeholder
    console.log('Login called with:', username, password)
    
    // Placeholder: Set mock data
    // const response = await loginApi({ username, password })
    // setTokenValue(response.access_token)
    // if (response.refresh_token) {
    //   setRefreshTokenValue(response.refresh_token)
    // }
    // await fetchUserInfo()
    
    throw new Error('Backend auth endpoints not implemented yet')
  }

  /**
   * Logout action
   */
  async function logout(): Promise<void> {
    // TODO: Call backend logout API if needed
    // await logoutApi()
    
    // Clear state
    user.value = null
    token.value = null
    refreshToken.value = null
    clearTokens()
  }

  /**
   * Set access token
   */
  function setTokenValue(newToken: string): void {
    token.value = newToken
    setToken(newToken)
  }

  /**
   * Set refresh token
   */
  function setRefreshTokenValue(newRefreshToken: string): void {
    refreshToken.value = newRefreshToken
    setRefreshToken(newRefreshToken)
  }

  /**
   * Refresh access token - will be implemented when backend is ready
   */
  async function refreshAccessToken(): Promise<void> {
    // TODO: Implement when backend /api/v1/auth/refresh is available
    // const currentRefreshToken = refreshToken.value
    // if (!currentRefreshToken) {
    //   throw new Error('No refresh token available')
    // }
    // const response = await refreshTokenApi({ refresh_token: currentRefreshToken })
    // setTokenValue(response.access_token)
    
    throw new Error('Backend auth endpoints not implemented yet')
  }

  /**
   * Fetch current user information
   */
  async function fetchUserInfo(): Promise<void> {
    // TODO: Implement when backend /api/v1/auth/me is available
    // const userInfo = await getCurrentUserApi()
    // user.value = userInfo
    
    throw new Error('Backend auth endpoints not implemented yet')
  }

  /**
   * Initialize auth state from stored token
   */
  async function initAuth(): Promise<void> {
    const storedToken = getToken()
    if (storedToken) {
      token.value = storedToken
      try {
        await fetchUserInfo()
      } catch {
        // If fetching user info fails, clear tokens
        await logout()
      }
    }
  }

  return {
    // State
    user,
    token,
    refreshToken,
    // Getters
    isAuthenticated,
    userInfo,
    // Actions
    login,
    logout,
    setTokenValue,
    setRefreshTokenValue,
    refreshAccessToken,
    fetchUserInfo,
    initAuth,
  }
})
