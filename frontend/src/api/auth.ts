/**
 * Authentication API endpoints
 */

import request from './index'
import type {
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
} from '@/types/auth'
import type { User } from '@/types/user'
import type { ApiResponse } from '@/types/api'

/**
 * User login
 * @param data Login credentials (username/email and password)
 * @returns Access token, refresh token, and expiration info
 */
export function login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
  return request({
    url: '/auth/login',
    method: 'post',
    data,
  })
}

/**
 * User logout
 * Invalidates the current session (if backend tracks sessions)
 */
export function logout(): Promise<ApiResponse<{ message: string }>> {
  return request({
    url: '/auth/logout',
    method: 'post',
  })
}

/**
 * Refresh access token using refresh token
 * @param data Refresh token
 * @returns New access token
 */
export function refreshToken(
  data: RefreshTokenRequest,
): Promise<ApiResponse<RefreshTokenResponse>> {
  return request({
    url: '/auth/refresh',
    method: 'post',
    data,
  })
}

/**
 * Get current authenticated user information
 * @returns User profile data
 */
export function getCurrentUser(): Promise<ApiResponse<User>> {
  return request({
    url: '/auth/me',
    method: 'get',
  })
}
