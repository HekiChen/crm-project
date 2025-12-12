<template>
  <div class="employee-detail">
    <el-page-header @back="handleBack" title="Back to Employees">
      <template #content>
        <span class="page-title">
          {{ employee ? `${employee.first_name} ${employee.last_name}` : 'Employee Details' }}
        </span>
      </template>
      <template #extra>
        <el-space v-if="isManagerOrAdmin && employee">
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
            <el-descriptions-item label="Employee Number">
              {{ employee.employee_number }}
            </el-descriptions-item>
            <el-descriptions-item label="Status">
              <el-tag :type="employee.is_active ? 'success' : 'info'" size="small">
                {{ employee.is_active ? 'Active' : 'Inactive' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="First Name">{{ employee.first_name }}</el-descriptions-item>
            <el-descriptions-item label="Last Name">{{ employee.last_name }}</el-descriptions-item>
            <el-descriptions-item label="Email">{{ employee.email }}</el-descriptions-item>
            <el-descriptions-item label="Hire Date">{{ formatDate(employee.hire_date) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- Work Information -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <span class="card-title">Work Information</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Position">
              <span v-if="employee.position">
                {{ employee.position.name }}
                <el-tag size="small" class="ml-2">{{ employee.position.code }}</el-tag>
              </span>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="Position Level">
              {{ employee.position?.level || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Department">
              <span 
                v-if="employee.department" 
                class="clickable-link" 
                @click="navigateToDepartment(employee.department.id)"
              >
                {{ employee.department.name }}
                <el-tag size="small" class="ml-2">{{ employee.department.code }}</el-tag>
              </span>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="Manager">
              <span 
                v-if="employee.manager" 
                class="clickable-link" 
                @click="navigateToEmployee(employee.manager.id)"
              >
                {{ employee.manager.first_name }} {{ employee.manager.last_name }}
                <el-tag size="small" class="ml-2">{{ employee.manager.employee_number }}</el-tag>
              </span>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item 
              v-if="employee.position?.description" 
              label="Position Description" 
              :span="2"
            >
              {{ employee.position.description }}
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
            <el-descriptions-item label="Address Line 1" :span="2">
              {{ employee.address1 || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Address Line 2" :span="2">
              {{ employee.address2 || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="City">{{ employee.city || '-' }}</el-descriptions-item>
            <el-descriptions-item label="State/Province">{{ employee.state || '-' }}</el-descriptions-item>
            <el-descriptions-item label="ZIP Code">{{ employee.zip_code || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- Timestamps -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <span class="card-title">Record Information</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Created At">
              {{ formatDateTime(employee.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="Updated At">
              {{ formatDateTime(employee.updated_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </template>
    </div>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="editDialogVisible"
      title="Edit Employee"
      width="700px"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <EmployeeForm
        ref="employeeFormRef"
        :model-value="employee"
        :positions="positions"
        :departments="departments"
        :active-employees="activeEmployees"
        @submit="handleEditSubmit"
      />
      <template #footer>
        <el-button @click="editDialogVisible = false" :disabled="submittingEdit">Cancel</el-button>
        <el-button
          type="primary"
          :loading="submittingEdit"
          @click="employeeFormRef?.handleSubmit()"
        >
          Save Changes
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'
import { 
  getEmployee, 
  updateEmployee, 
  deleteEmployee 
} from '@/api/employees'
import { getPositions } from '@/api/positions'
import { getDepartments } from '@/api/departments'
import { getEmployees } from '@/api/employees'
import { useAuth } from '@/composables/useAuth'
import type { Employee, EmployeeUpdate } from '@/types/employee'
import type { Position } from '@/types/position'
import type { Department } from '@/types/department'
import EmployeeForm from '@/components/EmployeeForm.vue'

defineOptions({
  name: 'EmployeeDetailPage',
})

const route = useRoute()
const router = useRouter()
const { isManagerOrAdmin } = useAuth()

const loading = ref(false)
const error = ref<string | null>(null)
const employee = ref<Employee | null>(null)

// Edit dialog state
const editDialogVisible = ref(false)
const employeeFormRef = ref<InstanceType<typeof EmployeeForm>>()
const submittingEdit = ref(false)

// Data for form dropdowns
const positions = ref<Position[]>([])
const departments = ref<Department[]>([])
const activeEmployees = ref<Employee[]>([])

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

const loadFormData = async () => {
  try {
    const [positionsRes, departmentsRes, employeesRes] = await Promise.all([
      getPositions({ page: 1, page_size: 1000 }),
      getDepartments({ page: 1, page_size: 1000 }),
      getEmployees({ page: 1, page_size: 1000, is_active: true }),
    ])

    if (positionsRes.data) {
      positions.value = positionsRes.data.data
    }
    if (departmentsRes.data) {
      departments.value = departmentsRes.data.data
    }
    if (employeesRes.data) {
      activeEmployees.value = employeesRes.data.data
    }
  } catch (error) {
    console.error('Error loading form data:', error)
  }
}

const handleBack = () => {
  router.push({ name: 'Employees' })
}

const handleEdit = () => {
  editDialogVisible.value = true
}

const handleEditSubmit = async (formData: EmployeeUpdate) => {
  if (!employee.value) return

  try {
    submittingEdit.value = true
    await updateEmployee(employee.value.id, formData)
    ElMessage.success('Employee updated successfully')
    editDialogVisible.value = false
    await fetchEmployee() // Reload employee data
  } catch (error: any) {
    console.error('Error updating employee:', error)
    const message = error.response?.data?.detail || 'Failed to update employee'
    ElMessage.error(message)
  } finally {
    submittingEdit.value = false
  }
}

const handleDelete = () => {
  if (!employee.value) return

  ElMessageBox.confirm(
    `Are you sure you want to delete employee "${employee.value.first_name} ${employee.value.last_name}"? This action will mark the employee as inactive.`,
    'Confirm Delete',
    {
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await deleteEmployee(employee.value!.id)
        ElMessage.success('Employee deleted successfully')
        handleBack()
      } catch (error) {
        console.error('Error deleting employee:', error)
        ElMessage.error('Failed to delete employee')
      }
    })
    .catch(() => {
      // User cancelled
    })
}

const handleDialogClosed = () => {
  employeeFormRef.value?.resetForm()
}

const navigateToEmployee = (id: string) => {
  router.push(`/employees/${id}`)
}

const navigateToDepartment = (id: string) => {
  router.push(`/departments/${id}`)
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

const formatDateTime = (dateString?: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchEmployee()
  loadFormData()
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

.clickable-link {
  color: var(--el-color-primary);
  cursor: pointer;
  text-decoration: none;
}

.clickable-link:hover {
  text-decoration: underline;
}

.ml-2 {
  margin-left: 8px;
}
</style>
