/**
 * Vue Router configuration
 */

import { createRouter, createWebHistory } from 'vue-router'
import { routes } from './routes'
import { authGuard } from './guards'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Restore scroll position or scroll to top
    if (savedPosition) {
      return savedPosition
    } else if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    } else {
      return { top: 0 }
    }
  },
})

// Global navigation guard
router.beforeEach(authGuard)

// Optional: Set page title based on route meta
router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  if (title) {
    document.title = `${title} - CRM System`
  } else {
    document.title = 'CRM System'
  }
})

export default router

