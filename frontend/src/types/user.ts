/**
 * User and Employee types
 */

import type { Role } from './role'

export interface User {
  id: number
  username: string
  email?: string
  full_name?: string
  is_active: boolean
  roles?: Role[]
  created_at?: string
  updated_at?: string
}

export interface Employee {
  id: number
  name: string
  email: string
  phone?: string
  department_id?: number
  position_id?: number
  hire_date?: string
  status?: string
  created_at?: string
  updated_at?: string
}
