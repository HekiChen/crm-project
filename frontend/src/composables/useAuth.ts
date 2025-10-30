/**
 * Authentication composable
 * Provides reusable authentication and role-checking utilities
 */

import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

/**
 * Composable for authentication and role checking
 * @returns Object with user data and role checking functions
 */
export function useAuth() {
  const authStore = useAuthStore()
  
  const user = computed(() => authStore.user)
  
  /**
   * Check if current user has manager role
   */
  const isManager = computed(() => {
    if (!user.value?.roles) return false
    return user.value.roles.some(role => 
      role.code.toLowerCase() === 'manager'
    )
  })
  
  /**
   * Check if current user has a specific role
   * @param roleCode - Role code to check (case-insensitive)
   * @returns true if user has the role, false otherwise
   */
  const hasRole = (roleCode: string): boolean => {
    if (!user.value?.roles) return false
    return user.value.roles.some(role => 
      role.code.toLowerCase() === roleCode.toLowerCase()
    )
  }
  
  return {
    user,
    isManager,
    hasRole
  }
}
