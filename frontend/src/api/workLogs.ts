/**
 * Work Logs API client
 */

import request from './index'
import type {
  WorkLog,
  WorkLogCreate,
  WorkLogUpdate,
  RateWorkLogRequest,
  WorkLogFilter,
  ExportWorkLogsRequest,
  ExportJob,
} from '@/types/workLog'
import type { ApiResponse, ApiListResponse } from '@/types/api'

/**
 * Get a single work log by ID
 * @param id - Work log ID
 * @returns Work log details
 */
export function getWorkLog(id: string): Promise<ApiResponse<WorkLog>> {
  return request({
    url: `/work-logs/${id}`,
    method: 'get',
  })
}

/**
 * Get list of work logs with optional filters
 * @param params - Filter parameters
 * @returns Paginated list of work logs
 */
export function getWorkLogs(params?: WorkLogFilter): Promise<ApiListResponse<WorkLog>> {
  return request({
    url: '/work-logs/',
    method: 'get',
    params,
  })
}

/**
 * Get team work logs (managers only)
 * @param params - Filter parameters
 * @returns Paginated list of team work logs
 */
export function getTeamWorkLogs(params?: WorkLogFilter): Promise<ApiListResponse<WorkLog>> {
  return request({
    url: '/work-logs/team',
    method: 'get',
    params,
  })
}

/**
 * Create a new work log
 * @param data - Work log data
 * @returns Created work log
 */
export function createWorkLog(data: WorkLogCreate): Promise<ApiResponse<WorkLog>> {
  return request({
    url: '/work-logs/',
    method: 'post',
    data,
  })
}

/**
 * Update an existing work log
 * @param id - Work log ID
 * @param data - Updated work log data
 * @returns Updated work log
 */
export function updateWorkLog(id: string, data: WorkLogUpdate): Promise<ApiResponse<WorkLog>> {
  return request({
    url: `/work-logs/${id}`,
    method: 'put',
    data,
  })
}

/**
 * Delete a work log (soft delete)
 * @param id - Work log ID
 * @returns Success message
 */
export function deleteWorkLog(id: string): Promise<ApiResponse<{ message: string }>> {
  return request({
    url: `/work-logs/${id}`,
    method: 'delete',
  })
}

/**
 * Rate a work log (managers only)
 * @param id - Work log ID
 * @param data - Rating data (1-5)
 * @returns Updated work log with rating
 */
export function rateWorkLog(
  id: string,
  data: RateWorkLogRequest
): Promise<ApiResponse<WorkLog>> {
  return request({
    url: `/work-logs/${id}/rate`,
    method: 'post',
    data,
  })
}

/**
 * Request work logs export
 * @param data - Export filters
 * @returns Export job information
 */
export function exportWorkLogs(data: ExportWorkLogsRequest): Promise<ApiResponse<ExportJob>> {
  return request({
    url: '/work-logs/export',
    method: 'post',
    data,
  })
}

/**
 * Get export job status
 * @param jobId - Export job ID
 * @returns Export job status
 */
export function getExportJob(jobId: string): Promise<ApiResponse<ExportJob>> {
  return request({
    url: `/work-logs/export/${jobId}`,
    method: 'get',
  })
}

/**
 * Download completed export file
 * @param jobId - Export job ID
 * @returns File blob
 */
export function downloadExport(jobId: string): Promise<Blob> {
  return request({
    url: `/work-logs/export/${jobId}/download`,
    method: 'get',
    responseType: 'blob',
  })
}
