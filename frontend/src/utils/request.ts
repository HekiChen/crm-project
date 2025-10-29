/**
 * Request helper functions
 */

import request from '@/api'
import type { AxiosRequestConfig, AxiosResponse } from 'axios'

/**
 * Generic GET request
 */
export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response: AxiosResponse<T> = await request.get(url, config)
  return response.data
}

/**
 * Generic POST request
 */
export async function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response: AxiosResponse<T> = await request.post(url, data, config)
  return response.data
}

/**
 * Generic PUT request
 */
export async function put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response: AxiosResponse<T> = await request.put(url, data, config)
  return response.data
}

/**
 * Generic PATCH request
 */
export async function patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response: AxiosResponse<T> = await request.patch(url, data, config)
  return response.data
}

/**
 * Generic DELETE request
 */
export async function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response: AxiosResponse<T> = await request.delete(url, config)
  return response.data
}
