/**
 * Position related types
 */

/**
 * Position entity
 */
export interface Position {
  id: string
  name: string
  code: string
  level?: number | null
  description?: string | null
  department_id?: string | null
  is_active: boolean
  created_at?: string
  updated_at?: string
  is_deleted?: boolean
}

/**
 * Position creation request
 */
export interface PositionCreate {
  name: string
  code: string
  level?: number | null
  description?: string | null
  department_id?: string | null
  is_active?: boolean
}

/**
 * Position update request
 */
export interface PositionUpdate {
  name?: string
  code?: string
  level?: number | null
  description?: string | null
  department_id?: string | null
  is_active?: boolean
}
