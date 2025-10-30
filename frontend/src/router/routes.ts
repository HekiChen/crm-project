/**
 * Route definitions
 */

import type { RouteRecordRaw } from 'vue-router'

export const routes: RouteRecordRaw[] = [
  // Public routes (no authentication required)
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      requiresAuth: false,
      title: 'Login',
    },
  },

  // Protected routes (authentication required)
  {
    path: '/',
    name: 'Root',
    redirect: '/dashboard',
    component: () => import('@/layouts/DefaultLayout.vue'),
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: {
          requiresAuth: true,
          title: 'Dashboard',
        },
      },
      {
        path: '/employees',
        name: 'Employees',
        component: () => import('@/views/EmployeesList.vue'),
        meta: {
          requiresAuth: true,
          title: 'Employees',
        },
      },
      {
        path: '/departments',
        name: 'Departments',
        component: () => import('@/views/DepartmentsList.vue'),
        meta: {
          requiresAuth: true,
          title: 'Departments',
        },
      },
      {
        path: '/roles',
        name: 'Roles',
        component: () => import('@/views/RolesList.vue'),
        meta: {
          requiresAuth: true,
          title: 'Roles',
        },
      },
      {
        path: '/roles/:id',
        name: 'RoleDetail',
        component: () => import('@/views/RoleDetail.vue'),
        meta: {
          requiresAuth: true,
          title: 'Role Details',
        },
      },
      {
        path: '/work-logs',
        name: 'WorkLogs',
        component: () => import('@/views/WorkLogsList.vue'),
        meta: {
          requiresAuth: true,
          title: 'Work Logs',
        },
      },
      // Department detail page
      {
        path: '/departments/:id',
        name: 'DepartmentDetail',
        component: () => import('@/views/DepartmentDetail.vue'),
        meta: {
          requiresAuth: true,
          title: 'Department Details',
        },
      },
      // Employee detail page
      {
        path: '/employees/:id',
        name: 'EmployeeDetail',
        component: () => import('@/views/EmployeeDetail.vue'),
        meta: {
          requiresAuth: true,
          title: 'Employee Details',
        },
      },
      // Add more protected routes here as needed
    ],
  },

  // 404 Not Found route (must be last)
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      requiresAuth: false,
      title: '404 Not Found',
    },
  },
]
