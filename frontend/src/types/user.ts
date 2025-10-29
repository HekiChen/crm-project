/**
 * User and Employee types
 */

import type { Role } from './role'

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  employee_number: string
  hire_date: string
  is_active: boolean
  roles: Role[]
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
