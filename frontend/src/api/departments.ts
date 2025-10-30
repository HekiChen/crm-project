/**
 * Department API endpoints
 */

import request from './index'
import type { Department, DepartmentCreate, DepartmentUpdate, DepartmentListParams } from '@/types/department'
import type { ApiResponse, ApiListResponse } from '@/types/api'

/**
 * Get paginated list of departments
 * @param params - Query parameters for filtering and pagination
 * @returns Paginated list of departments
 */
export function getDepartments(params?: DepartmentListParams): Promise<ApiListResponse<Department>> {
  return request({
    url: '/departments/',
    method: 'get',
    params,
  })
}

/**
 * Get single department by ID
 * @param id - Department ID
 * @returns Department details
 */
export function getDepartment(id: string): Promise<ApiResponse<Department>> {
  return request({
    url: `/departments/${id}`,
    method: 'get',
  })
}

/**
 * Create a new department
 * @param data - Department creation data
 * @returns Created department
 */
export function createDepartment(data: DepartmentCreate): Promise<ApiResponse<Department>> {
  return request({
    url: '/departments/',
    method: 'post',
    data,
  })
}

/**
 * Update an existing department
 * @param id - Department ID
 * @param data - Department update data
 * @returns Updated department
 */
export function updateDepartment(id: string, data: DepartmentUpdate): Promise<ApiResponse<Department>> {
  return request({
    url: `/departments/${id}`,
    method: 'patch',
    data,
  })
}

/**
 * Delete a department (soft delete)
 * @param id - Department ID
 * @returns Success message
 */
export function deleteDepartment(id: string): Promise<ApiResponse<{ message: string }>> {
  return request({
    url: `/departments/${id}`,
    method: 'delete',
  })
}

/**
 * Get child departments
 * @param id - Department ID
 * @returns List of child departments
 */
export function getDepartmentChildren(id: string): Promise<ApiResponse<Department[]>> {
  return request({
    url: `/departments/${id}/children`,
    method: 'get',
  })
}

/**
 * Get parent department
 * @param id - Department ID
 * @returns Parent department
 */
export function getDepartmentParent(id: string): Promise<ApiResponse<Department>> {
  return request({
    url: `/departments/${id}/parent`,
    method: 'get',
  })
}
