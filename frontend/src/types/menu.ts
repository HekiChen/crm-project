/**
 * Menu types
 */

export interface Menu {
  id: number
  name: string
  path?: string
  component?: string
  icon?: string
  parent_id?: number | null
  sort_order: number
  is_visible: boolean
  permission_code?: string
  meta?: Record<string, unknown>
  created_at?: string
  updated_at?: string
  children?: Menu[]
}

export interface MenuTree extends Menu {
  children: MenuTree[]
}
