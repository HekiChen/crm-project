<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1 class="dashboard-title">Dashboard</h1>
      <p v-if="user" class="dashboard-welcome">Welcome back, {{ user.full_name }}!</p>
    </div>

    <el-row :gutter="20" class="dashboard-cards">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="summary-card">
          <div class="card-content">
            <div class="card-icon employees">
              <el-icon :size="32"><User /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-value">{{ summaryData.totalEmployees }}</div>
              <div class="card-label">Total Employees</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="summary-card">
          <div class="card-content">
            <div class="card-icon departments">
              <el-icon :size="32"><OfficeBuilding /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-value">{{ summaryData.totalDepartments }}</div>
              <div class="card-label">Departments</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="summary-card">
          <div class="card-content">
            <div class="card-icon roles">
              <el-icon :size="32"><UserFilled /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-value">{{ summaryData.totalRoles }}</div>
              <div class="card-label">Roles</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="summary-card">
          <div class="card-content">
            <div class="card-icon activities">
              <el-icon :size="32"><Clock /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-value">{{ summaryData.recentActivities }}</div>
              <div class="card-label">Recent Activities</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="dashboard-content">
      <el-col :xs="24" :md="16">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>Quick Actions</span>
            </div>
          </template>
          <div class="quick-actions">
            <p class="placeholder-text">
              Quick action buttons will be added here for common tasks.
            </p>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="8">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>System Info</span>
            </div>
          </template>
          <div class="system-info">
            <div class="info-item">
              <span class="info-label">Your Role:</span>
              <span class="info-value">
                {{ user?.roles && user.roles.length > 0 ? (user.roles[0]?.name || 'Unknown') : 'No role assigned' }}
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">Employee #:</span>
              <span class="info-value">{{ user?.employee_number }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Status:</span>
              <el-tag :type="user?.is_active ? 'success' : 'danger'" size="small">
                {{ user?.is_active ? 'Active' : 'Inactive' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { User, OfficeBuilding, UserFilled, Clock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

defineOptions({
  name: 'DashboardPage',
})

const authStore = useAuthStore()

// Computed
const user = computed(() => authStore.user)

// Summary data (placeholder - will be fetched from API in the future)
const summaryData = ref({
  totalEmployees: 0,
  totalDepartments: 0,
  totalRoles: 0,
  recentActivities: 0,
})

// Lifecycle hooks
onMounted(() => {
  loadDashboardData()
})

// Methods
const loadDashboardData = async () => {
  // TODO: Fetch real data from API
  // For now, show placeholder data
  summaryData.value = {
    totalEmployees: 42,
    totalDepartments: 8,
    totalRoles: 5,
    recentActivities: 23,
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 24px;
}

.dashboard-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.dashboard-welcome {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.dashboard-cards {
  margin-bottom: 20px;
}

.summary-card {
  cursor: pointer;
  transition: transform 0.3s;
}

.summary-card:hover {
  transform: translateY(-4px);
}

.card-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.card-icon.employees {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.card-icon.departments {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.card-icon.roles {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.card-icon.activities {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.card-info {
  flex: 1;
}

.card-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.card-label {
  font-size: 14px;
  color: #909399;
}

.dashboard-content {
  margin-top: 20px;
}

.card-header {
  font-weight: 600;
  color: #303133;
}

.quick-actions {
  padding: 20px 0;
}

.placeholder-text {
  text-align: center;
  color: #909399;
  font-size: 14px;
}

.system-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: #606266;
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

/* Responsive design */
@media (max-width: 768px) {
  .dashboard-title {
    font-size: 24px;
  }

  .card-value {
    font-size: 24px;
  }

  .card-icon {
    width: 48px;
    height: 48px;
  }
}
</style>
