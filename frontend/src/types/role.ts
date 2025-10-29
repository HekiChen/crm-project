/**
 * Role and Permission types
 */

export interface Role {
  id: number
  name: string
  code: string
  description?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
  permissions?: Permission[]
}

export interface Permission {
  id: number
  name: string
  code: string
  resource: string
  action: string
  description?: string
  created_at?: string
  updated_at?: string
}

export interface RolePermission {
  role_id: number
  permission_id: number
  granted_at?: string
}
