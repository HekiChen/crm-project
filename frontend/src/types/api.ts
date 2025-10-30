/**
 * Base API response types
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface ApiResponse<T = any> {
  status?: number
  message?: string
  data: T
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface ApiListResponse<T = any> {
  status?: number
  message?: string
  data: {
    data: T[]
    total: number
    page?: number
    page_size?: number
    total_pages?: number
    has_next?: boolean
    has_previous?: boolean
  }
}

export interface ApiError {
  status: number
  message: string
  detail?: unknown
}

export interface PaginationParams {
  page?: number
  page_size?: number
  skip?: number
  limit?: number
}
