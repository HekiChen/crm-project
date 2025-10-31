/**
 * Role type definitions matching backend schemas
 */

export interface Role {
  id: string
  name: string
  code: string
  description: string | null
  is_system_role: boolean
  created_at: string
  updated_at: string
  is_deleted: boolean
  deleted_at: string | null
  created_by_id: string | null
  updated_by_id: string | null
}

export interface RoleCreate {
  name: string
  code: string
  description?: string | null
}

export interface RoleUpdate {
  name?: string
  description?: string | null
  // Note: code is intentionally excluded - it's immutable after creation
}

export interface RoleEmployee {
  id: string
  employee_id: string
  employee_name: string
  email: string
  position: string | null
  department: string | null
  assigned_at: string
  assigned_by_id: string | null
  created_at: string
  updated_at: string
}

export interface RolePermission {
  id: string
  role_id: string
  menu_id: string
  menu_name: string
  menu_path: string
  menu_type: string
  menu_icon: string | null
  parent_id: string | null
  can_read: boolean
  can_write: boolean
  can_delete: boolean
  created_at: string
  updated_at: string
  created_by_id: string | null
  updated_by_id: string | null
}
