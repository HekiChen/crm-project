/**
 * Employee API client
 */

import request from './index'
import type { Employee, EmployeeCreate, EmployeeUpdate } from '@/types/employee'
import type { ApiResponse, ApiListResponse } from '@/types/api'

/**
 * Employee list query parameters
 */
export interface EmployeeListParams {
  page?: number
  page_size?: number
  position_id?: string
  department_id?: string
  is_active?: boolean
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

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
 * Get list of employees with optional filters
 * @param params - Query parameters (pagination, filters, search)
 * @returns Paginated list of employees
 */
export function getEmployees(params?: EmployeeListParams): Promise<ApiListResponse<Employee>> {
  return request({
    url: '/employees/',
    method: 'get',
    params,
  })
}

/**
 * Create a new employee
 * @param data - Employee data
 * @returns Created employee
 */
export function createEmployee(data: EmployeeCreate): Promise<ApiResponse<Employee>> {
  return request({
    url: '/employees/',
    method: 'post',
    data,
  })
}

/**
 * Update an existing employee
 * @param id - Employee ID
 * @param data - Updated employee data
 * @returns Updated employee
 */
export function updateEmployee(id: string, data: EmployeeUpdate): Promise<ApiResponse<Employee>> {
  return request({
    url: `/employees/${id}`,
    method: 'put',
    data,
  })
}

/**
 * Delete an employee (soft delete)
 * @param id - Employee ID
 * @returns Success message
 */
export function deleteEmployee(id: string): Promise<ApiResponse<{ message: string }>> {
  return request({
    url: `/employees/${id}`,
    method: 'delete',
  })
}
