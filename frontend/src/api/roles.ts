/**
 * Role API endpoints
 */

import request from './index'
import type { Role, RoleCreate, RoleUpdate, RoleEmployee, RolePermission } from '@/types/role'
import type { ApiResponse, ApiListResponse } from '@/types/api'

/**
 * Get paginated list of roles
 * @param params - Query parameters for filtering and pagination
 * @returns Paginated list of roles
 */
export function getRoles(params?: {
  page?: number
  page_size?: number
  is_system_role?: boolean
  search?: string
}): Promise<ApiListResponse<Role>> {
  return request({
    url: '/roles/',
    method: 'get',
    params,
  })
}

/**
 * Get single role by ID
 * @param id - Role ID
 * @returns Role details
 */
export function getRole(id: string): Promise<ApiResponse<Role>> {
  return request({
    url: `/roles/${id}`,
    method: 'get',
  })
}

/**
 * Create a new role
 * @param data - Role creation data
 * @returns Created role
 */
export function createRole(data: RoleCreate): Promise<ApiResponse<Role>> {
  return request({
    url: '/roles/',
    method: 'post',
    data,
  })
}

/**
 * Update an existing role
 * @param id - Role ID
 * @param data - Role update data
 * @returns Updated role
 */
export function updateRole(id: string, data: RoleUpdate): Promise<ApiResponse<Role>> {
  return request({
    url: `/roles/${id}`,
    method: 'patch',
    data,
  })
}

/**
 * Delete a role (soft delete)
 * @param id - Role ID
 * @returns Success message
 */
export function deleteRole(id: string): Promise<ApiResponse<{ message: string }>> {
  return request({
    url: `/roles/${id}`,
    method: 'delete',
  })
}

/**
 * Get employees assigned to a role
 * @param id - Role ID
 * @returns List of employees assigned to the role
 */
export function getRoleEmployees(id: string): Promise<ApiResponse<RoleEmployee[]>> {
  return request({
    url: `/roles/${id}/employees`,
    method: 'get',
  })
}

/**
 * Get menu permissions for a role
 * @param id - Role ID
 * @returns List of menu permissions for the role
 */
export function getRolePermissions(id: string): Promise<ApiResponse<RolePermission[]>> {
  return request({
    url: `/roles/${id}/permissions`,
    method: 'get',
  })
}

/**
 * Update a specific permission for a role and menu
 * @param roleId - Role ID
 * @param menuId - Menu ID
 * @param data - Permission update data
 * @returns Updated permission
 */
export function updateRolePermission(
  roleId: string,
  menuId: string,
  data: {
    can_read: boolean
    can_write: boolean
    can_delete: boolean
  }
): Promise<ApiResponse<RolePermission>> {
  return request({
    url: `/roles/${roleId}/permissions/${menuId}`,
    method: 'patch',
    data,
  })
}
