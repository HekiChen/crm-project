/**
 * Work Log types
 */

/**
 * Work log type enum
 */
export enum LogType {
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly',
  YEARLY = 'yearly',
}

/**
 * Work log model
 */
export interface WorkLog {
  id: string
  employee_id: string
  log_type: LogType
  start_date: string // ISO date string
  end_date: string // ISO date string
  progress: string
  issues?: string | null
  plans?: string | null
  rating?: number | null // 1-5 stars
  rated_by?: string | null // Employee ID of manager who rated
  rated_at?: string | null // ISO datetime string
  created_at: string
  updated_at: string
  is_deleted: boolean
  // Relationships
  employee?: {
    id: string
    first_name: string
    last_name: string
    email: string
  }
  rater?: {
    id: string
    first_name: string
    last_name: string
    email: string
  }
}

/**
 * Create work log request
 */
export interface WorkLogCreate {
  log_type: LogType
  start_date: string // Date in YYYY-MM-DD format
  progress: string
  issues?: string | null
  plans?: string | null
}

/**
 * Update work log request
 */
export interface WorkLogUpdate {
  progress?: string
  issues?: string | null
  plans?: string | null
}

/**
 * Rate work log request
 */
export interface RateWorkLogRequest {
  rating: number // 1-5
}

/**
 * Work log filter parameters
 */
export interface WorkLogFilter {
  employee_id?: string
  log_type?: LogType
  start_date?: string
  end_date?: string
  has_rating?: boolean
  page?: number
  page_size?: number
}

/**
 * Export work logs request
 */
export interface ExportWorkLogsRequest {
  start_date?: string
  end_date?: string
  log_type?: LogType
  employee_id?: string
  has_rating?: boolean
}

/**
 * Export job status
 */
export interface ExportJob {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  file_path?: string | null
  error_message?: string | null
  created_at: string
  updated_at: string
}
