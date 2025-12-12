/**
 * Router navigation guards
 */

import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

/**
 * Authentication guard
 * Checks if user is authenticated before allowing access to protected routes
 */
export async function authGuard(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext,
): Promise<void> {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  // If route doesn't require auth, allow access
  if (!requiresAuth) {
    // If user is authenticated and trying to access login page, redirect to dashboard
    if (to.name === 'Login' && authStore.isAuthenticated) {
      next({ name: 'Dashboard' })
      return
    }
    next()
    return
  }

  // Route requires auth - check if user is authenticated
  // The user should already be loaded by initAuth() in main.ts
  // Wait for initialization to complete if it's in progress
  if (authStore.isInitializing) {
    // Wait a bit for initialization to complete
    await new Promise(resolve => setTimeout(resolve, 50))
  }
  
  // Only fetch if token exists but user is still null (edge case / race condition)
  if (authStore.token && !authStore.user && !authStore.isInitializing) {
    try {
      await authStore.fetchUserInfo()
    } catch (error) {
      // Failed to fetch user info - will redirect to login below
      console.error('Failed to fetch user info in auth guard:', error)
    }
  }

  if (!authStore.isAuthenticated) {
    // Not authenticated - redirect to login (unless already going to login)
    if (to.name !== 'Login') {
      next({
        name: 'Login',
        query: {
          redirect: to.fullPath, // Save the attempted URL for redirecting after login
        },
      })
    } else {
      next()
    }
    return
  }

  // User is authenticated, allow access
  next()
}

/**
 * Permission guard (optional - for future use)
 * Checks if user has required permissions for a route
 */
export function permissionGuard(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext,
): void {
  const authStore = useAuthStore()
  const requiredPermission = to.meta.permission as string | undefined

  // If no permission required, allow access
  if (!requiredPermission) {
    next()
    return
  }

  // Check if user has the required permission
  // TODO: Implement actual permission check when user roles/permissions are available
  const hasPermission = authStore.user?.roles?.some((role) => {
    // This is a placeholder - actual implementation depends on role structure
    return role.name === requiredPermission || role.name === 'admin'
  })

  if (hasPermission) {
    next()
  } else {
    // User doesn't have permission - redirect to 403 or dashboard
    next({ name: 'Dashboard' })
  }
}
