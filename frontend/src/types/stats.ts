/**
 * Dashboard statistics data types
 */

/**
 * Dashboard statistics response from backend
 */
export interface DashboardStats {
  /** Total number of active employees */
  total_employees: number

  /** Total number of active departments */
  total_departments: number

  /** Total number of active roles */
  total_roles: number

  /** Number of work log activities in the last 7 days */
  recent_activities: number
}
