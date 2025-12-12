/**
 * Authentication Store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { getToken, setToken, getRefreshToken, setRefreshToken, clearTokens } from '@/utils/token'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(getToken())
  const refreshToken = ref<string | null>(getRefreshToken())
  const isInitializing = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userInfo = computed(() => user.value)

  // Actions

  /**
   * Login action
   * @param username - User's username or email
   * @param password - User's password
   */
  async function login(username: string, password: string): Promise<void> {
    try {
      const response = await authApi.login({ username, password })
      const loginData = response.data

      // Set tokens
      setTokenValue(loginData.access_token)
      if (loginData.refresh_token) {
        setRefreshTokenValue(loginData.refresh_token)
      }

      // Fetch user info
      await fetchUserInfo()
    } catch (error) {
      // Clear any partial state on error
      user.value = null
      token.value = null
      refreshToken.value = null
      clearTokens()
      throw error
    }
  }

  /**
   * Logout action
   */
  async function logout(): Promise<void> {
    try {
      // Call backend logout API
      await authApi.logout()
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API error:', error)
    } finally {
      // Clear state regardless of API result
      user.value = null
      token.value = null
      refreshToken.value = null
      clearTokens()
    }
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
   * Refresh access token
   */
  async function refreshAccessToken(): Promise<void> {
    const currentRefreshToken = refreshToken.value
    if (!currentRefreshToken) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await authApi.refreshToken({ refresh_token: currentRefreshToken })
      setTokenValue(response.data.access_token)
    } catch (error) {
      // If refresh fails, logout user
      await logout()
      throw error
    }
  }

  /**
   * Fetch current user information
   */
  async function fetchUserInfo(): Promise<void> {
    try {
      const response = await authApi.getCurrentUser()
      user.value = response.data
    } catch (error) {
      console.error('Failed to fetch user info:', error)
      // If fetching user info fails (e.g., token invalid), clear tokens
      user.value = null
      token.value = null
      refreshToken.value = null
      clearTokens()
      throw error
    }
  }

  /**
   * Initialize auth state from stored token
   */
  async function initAuth(): Promise<void> {
    const storedToken = getToken()
    if (storedToken) {
      token.value = storedToken
      isInitializing.value = true
      try {
        await fetchUserInfo()
      } catch {
        // If fetching user info fails, clear tokens
        await logout()
      } finally {
        isInitializing.value = false
      }
    }
  }

  return {
    // State
    user,
    token,
    refreshToken,
    isInitializing,
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
