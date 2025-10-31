/**
 * Department related types
 */

/**
 * Manager summary for department display
 */
export interface ManagerSummary {
  id: string
  first_name: string
  last_name: string
}

/**
 * Department summary for relationships
 */
export interface DepartmentSummary {
  id: string
  name: string
  code: string
}

/**
 * Department entity
 */
export interface Department {
  id: string
  name: string
  code: string
  description?: string | null
  parent_id?: string | null
  parent?: DepartmentSummary | null
  manager_id?: string | null
  manager?: ManagerSummary | null
  is_active: boolean
  children?: DepartmentSummary[] | null
  created_at?: string
  updated_at?: string
  is_deleted?: boolean
}

/**
 * Department creation request
 */
export interface DepartmentCreate {
  name: string
  code: string
  description?: string | null
  parent_id?: string | null
  manager_id?: string | null
  is_active?: boolean
}

/**
 * Department update request
 */
export interface DepartmentUpdate {
  name?: string
  code?: string
  description?: string | null
  parent_id?: string | null
  manager_id?: string | null
  is_active?: boolean
}

/**
 * Department list query parameters
 */
export interface DepartmentListParams {
  page?: number
  page_size?: number
  skip?: number
  limit?: number
  search?: string
  is_active?: boolean
}
