/**
 * Position API client
 */

import request from './index'
import type { Position, PositionCreate, PositionUpdate } from '@/types/position'
import type { ApiResponse, ApiListResponse } from '@/types/api'

/**
 * Position list query parameters
 */
export interface PositionListParams {
  page?: number
  page_size?: number
  department_id?: string
  is_active?: boolean
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

/**
 * Get a single position by ID
 * @param id - Position ID
 * @returns Position details
 */
export function getPosition(id: string): Promise<ApiResponse<Position>> {
  return request({
    url: `/positions/${id}`,
    method: 'get',
  })
}

/**
 * Get list of positions with optional filters
 * @param params - Query parameters (pagination, filters, search)
 * @returns Paginated list of positions
 */
export function getPositions(params?: PositionListParams): Promise<ApiListResponse<Position>> {
  return request({
    url: '/positions/',
    method: 'get',
    params,
  })
}

/**
 * Create a new position
 * @param data - Position data
 * @returns Created position
 */
export function createPosition(data: PositionCreate): Promise<ApiResponse<Position>> {
  return request({
    url: '/positions/',
    method: 'post',
    data,
  })
}

/**
 * Update an existing position
 * @param id - Position ID
 * @param data - Updated position data
 * @returns Updated position
 */
export function updatePosition(id: string, data: PositionUpdate): Promise<ApiResponse<Position>> {
  return request({
    url: `/positions/${id}`,
    method: 'put',
    data,
  })
}

/**
 * Delete a position (soft delete)
 * @param id - Position ID
 * @returns Success message
 */
export function deletePosition(id: string): Promise<ApiResponse<{ message: string }>> {
  return request({
    url: `/positions/${id}`,
    method: 'delete',
  })
}
