/**
 * Health check API
 */

import { get } from '@/utils/request'

export interface HealthResponse {
  status: string
  timestamp?: string
}

/**
 * Check API health status
 */
export async function checkHealth(): Promise<HealthResponse> {
  return get<HealthResponse>('/health')
}
