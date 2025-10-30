<template>
  <el-container class="default-layout">
    <!-- Sidebar -->
    <el-aside :width="sidebarCollapsed ? '64px' : '240px'" class="layout-sidebar">
      <div class="sidebar-header">
        <h2 v-if="!sidebarCollapsed" class="sidebar-title">CRM</h2>
        <h2 v-else class="sidebar-title-collapsed">C</h2>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="sidebarCollapsed"
        class="sidebar-menu"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <template #title>Dashboard</template>
        </el-menu-item>

        <el-menu-item index="/employees">
          <el-icon><User /></el-icon>
          <template #title>Employees</template>
        </el-menu-item>

        <el-menu-item index="/departments">
          <el-icon><OfficeBuilding /></el-icon>
          <template #title>Departments</template>
        </el-menu-item>

        <!-- Roles menu - only show for managers and admins -->
        <el-menu-item v-if="isManagerOrAdmin" index="/roles">
          <el-icon><Avatar /></el-icon>
          <template #title>Roles</template>
        </el-menu-item>

        <el-menu-item index="/work-logs">
          <el-icon><Calendar /></el-icon>
          <template #title>Work Logs</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- Main content area -->
    <el-container>
      <!-- Header -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-button
            :icon="sidebarCollapsed ? Expand : Fold"
            circle
            @click="toggleSidebar"
          />
        </div>

        <div class="header-right">
          <!-- User dropdown -->
          <el-dropdown @command="handleUserCommand">
            <div class="user-info">
              <el-avatar :size="32" :icon="UserFilled" />
              <span v-if="user" class="user-name">{{ user.full_name }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <div class="user-details">
                    <div>{{ user?.email }}</div>
                    <div class="user-role">{{ user?.employee_number }}</div>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  Logout
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- Main content -->
      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  HomeFilled,
  UserFilled,
  SwitchButton,
  Expand,
  Fold,
  User,
  OfficeBuilding,
  Avatar,
  Calendar,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useAuth } from '@/composables/useAuth'

defineOptions({
  name: 'DefaultLayout',
})

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { user, isManagerOrAdmin } = useAuth()

// Sidebar state
const sidebarCollapsed = ref(false)

// Computed
const activeMenu = computed(() => route.path)

// Methods
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const handleUserCommand = async (command: string) => {
  if (command === 'logout') {
    try {
      await authStore.logout()
      ElMessage.success('Logged out successfully')
      router.push('/login')
    } catch (error) {
      console.error('Logout error:', error)
      ElMessage.error('Logout failed')
    }
  }
}
</script>

<style scoped>
.default-layout {
  height: 100vh;
}

.layout-sidebar {
  background: #304156;
  color: white;
  transition: width 0.3s;
  overflow-x: hidden;
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-title {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  padding: 0 20px;
}

.sidebar-title-collapsed {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.sidebar-menu {
  border-right: none;
  background: #304156;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 240px;
}

:deep(.el-menu-item) {
  color: #bfcbd9;
}

:deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: white;
}

:deep(.el-menu-item.is-active) {
  background: #409eff !important;
  color: white;
}

.layout-header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.3s;
}

.user-info:hover {
  background: #f5f7fa;
}

.user-name {
  font-size: 14px;
  color: #303133;
}

.user-details {
  padding: 4px 0;
}

.user-role {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.layout-main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

/* Page transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Responsive design */
@media (max-width: 768px) {
  .user-name {
    display: none;
  }

  .layout-main {
    padding: 12px;
  }
}
</style>
