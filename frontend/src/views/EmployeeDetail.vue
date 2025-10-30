<template>
  <div class="employee-detail">
    <el-page-header @back="handleBack" title="Back">
      <template #content>
        <span class="page-title">
          {{ employee ? `${employee.first_name} ${employee.last_name}` : 'Employee Details' }}
        </span>
      </template>
      <template #extra>
        <el-space v-if="isManager && employee">
          <el-button @click="handleEdit">
            <el-icon><Edit /></el-icon>
            Edit
          </el-button>
          <el-button type="danger" @click="handleDelete">
            <el-icon><Delete /></el-icon>
            Delete
          </el-button>
        </el-space>
      </template>
    </el-page-header>

    <div v-loading="loading" class="content">
      <!-- Error State -->
      <el-card v-if="error" shadow="never">
        <el-empty :description="error">
          <el-button type="primary" @click="fetchEmployee">Retry</el-button>
          <el-button @click="handleBack">Back to List</el-button>
        </el-empty>
      </el-card>

      <!-- Content -->
      <template v-else-if="employee">
        <!-- Basic Information -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <span class="card-title">Basic Information</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="First Name">{{ employee.first_name }}</el-descriptions-item>
            <el-descriptions-item label="Last Name">{{ employee.last_name }}</el-descriptions-item>
            <el-descriptions-item label="Email">{{ employee.email }}</el-descriptions-item>
            <el-descriptions-item label="Employee Number">{{ employee.employee_number }}</el-descriptions-item>
            <el-descriptions-item label="Hire Date">{{ formatDate(employee.hire_date) }}</el-descriptions-item>
            <el-descriptions-item label="Status">
              <el-tag :type="employee.is_active ? 'success' : 'info'" size="small">
                {{ employee.is_active ? 'Active' : 'Inactive' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- Contact Information -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <span class="card-title">Contact Information</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Phone">{{ employee.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="Country">{{ employee.country || '-' }}</el-descriptions-item>
            <el-descriptions-item label="Address 1" :span="2">{{ employee.address1 || '-' }}</el-descriptions-item>
            <el-descriptions-item label="Address 2" :span="2">{{ employee.address2 || '-' }}</el-descriptions-item>
            <el-descriptions-item label="City">{{ employee.city || '-' }}</el-descriptions-item>
            <el-descriptions-item label="State">{{ employee.state || '-' }}</el-descriptions-item>
            <el-descriptions-item label="ZIP Code">{{ employee.zip_code || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- Position Information -->
        <el-card v-if="employee.position" shadow="never" class="info-card">
          <template #header>
            <span class="card-title">Position Information</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Position Name">{{ employee.position.name }}</el-descriptions-item>
            <el-descriptions-item label="Position Code">{{ employee.position.code }}</el-descriptions-item>
            <el-descriptions-item label="Level">{{ employee.position.level || '-' }}</el-descriptions-item>
            <el-descriptions-item label="Description" :span="2">
              {{ employee.position.description || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- Work Assignments -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <span class="card-title">Work Assignments</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Department ID">
              {{ employee.department_id || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Manager ID">
              {{ employee.manager_id || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'
import { getEmployee } from '@/api/employees'
import { useAuth } from '@/composables/useAuth'
import type { Employee } from '@/types/employee'

defineOptions({
  name: 'EmployeeDetailPage',
})

const route = useRoute()
const router = useRouter()
const { isManager } = useAuth()

const loading = ref(false)
const error = ref<string | null>(null)
const employee = ref<Employee | null>(null)

const fetchEmployee = async () => {
  const id = route.params.id as string
  if (!id) {
    error.value = 'Invalid employee ID'
    return
  }

  loading.value = true
  error.value = null

  try {
    const response = await getEmployee(id)
    employee.value = response.data
  } catch (err) {
    console.error('Failed to fetch employee:', err)
    const errorResponse = err as { response?: { status?: number } }
    if (errorResponse.response?.status === 404) {
      error.value = 'Employee not found'
    } else {
      error.value = 'Failed to load employee details'
    }
  } finally {
    loading.value = false
  }
}

const handleBack = () => {
  router.push({ name: 'Employees' })
}

const handleEdit = () => {
  ElMessage.info('Edit employee feature coming soon')
}

const handleDelete = () => {
  ElMessage.info('Delete employee feature coming soon')
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString()
}

onMounted(() => {
  fetchEmployee()
})
</script>

<style scoped>
.employee-detail {
  padding: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
}

.content {
  margin-top: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}
</style>
