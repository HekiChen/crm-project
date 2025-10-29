/**
 * Token management utilities
 */

const TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

/**
 * Get access token from sessionStorage
 */
export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

/**
 * Set access token in sessionStorage
 */
export function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token)
}

/**
 * Remove access token from sessionStorage
 */
export function removeToken(): void {
  sessionStorage.removeItem(TOKEN_KEY)
}

/**
 * Get refresh token from sessionStorage
 */
export function getRefreshToken(): string | null {
  return sessionStorage.getItem(REFRESH_TOKEN_KEY)
}

/**
 * Set refresh token in sessionStorage
 */
export function setRefreshToken(token: string): void {
  sessionStorage.setItem(REFRESH_TOKEN_KEY, token)
}

/**
 * Remove refresh token from sessionStorage
 */
export function removeRefreshToken(): void {
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
}

/**
 * Clear all tokens
 */
export function clearTokens(): void {
  removeToken()
  removeRefreshToken()
}
