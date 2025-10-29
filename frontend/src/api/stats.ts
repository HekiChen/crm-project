/**
 * Statistics API endpoints
 */

import request from './index'
import type { DashboardStats } from '@/types/stats'
import type { ApiResponse } from '@/types/api'

/**
 * Get dashboard statistics
 * @returns Dashboard statistics including employee, department, role counts and recent activities
 */
export function getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
  return request({
    url: '/stats/dashboard',
    method: 'get',
  })
}
