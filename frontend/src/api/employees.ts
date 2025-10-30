/**
 * Employee API client
 */

import request from './index'
import type { Employee } from '@/types/employee'
import type { ApiResponse } from '@/types/api'

/**
 * Get a single employee by ID
 * @param id - Employee ID
 * @returns Employee details
 */
export function getEmployee(id: string): Promise<ApiResponse<Employee>> {
  return request({
    url: `/employees/${id}`,
    method: 'get',
  })
}
