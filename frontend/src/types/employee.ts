/**
 * Employee related types
 */

/**
 * Position entity
 */
export interface Position {
  id: string
  name: string
  code: string
  level?: string | null
  description?: string | null
  created_at?: string
  updated_at?: string
  is_deleted?: boolean
}

/**
 * Department summary for employee display
 */
export interface DepartmentSummary {
  id: string
  name: string
  code: string
}

/**
 * Manager/Employee summary for display
 */
export interface ManagerSummary {
  id: string
  first_name: string
  last_name: string
  employee_number: string
}

/**
 * Employee entity
 */
export interface Employee {
  id: string
  first_name: string
  last_name: string
  email: string
  employee_number: string
  hire_date: string
  position_id?: string | null
  position?: Position | null
  department_id?: string | null
  department?: DepartmentSummary | null
  manager_id?: string | null
  manager?: ManagerSummary | null
  phone?: string | null
  address1?: string | null
  address2?: string | null
  city?: string | null
  state?: string | null
  zip_code?: string | null
  country?: string | null
  is_active?: boolean
  created_at?: string
  updated_at?: string
  is_deleted?: boolean
  deleted_at?: string | null
  created_by_id?: string | null
  updated_by_id?: string | null
}

/**
 * Employee creation request
 */
export interface EmployeeCreate {
  first_name: string
  last_name: string
  email: string
  employee_number: string
  hire_date: string
  position_id?: string | null
  department_id?: string | null
  manager_id?: string | null
  phone?: string | null
  address1?: string | null
  address2?: string | null
  city?: string | null
  state?: string | null
  zip_code?: string | null
  country?: string | null
  is_active?: boolean
}

/**
 * Employee update request
 */
export interface EmployeeUpdate {
  first_name?: string
  last_name?: string
  email?: string
  employee_number?: string
  hire_date?: string
  position_id?: string | null
  department_id?: string | null
  manager_id?: string | null
  phone?: string | null
  address1?: string | null
  address2?: string | null
  city?: string | null
  state?: string | null
  zip_code?: string | null
  country?: string | null
  is_active?: boolean
}
