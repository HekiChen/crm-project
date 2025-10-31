/**
 * Employee API client
 */

import request from './index'
import type { Employee } from '@/types/employee'
import type { ApiResponse, ApiListResponse } from '@/types/api'

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

/**
 * Get list of all employees
 * @param params - Query parameters (pagination, filters)
 * @returns List of employees
 */
export function getEmployees(params?: { page?: number; page_size?: number }): Promise<ApiListResponse<Employee>> {
  return request({
    url: '/employees/',
    method: 'get',
    params,
  })
}
