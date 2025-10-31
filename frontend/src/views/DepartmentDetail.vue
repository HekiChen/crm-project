<template>
  <div class="department-detail">
    <el-page-header @back="handleBack" title="Back to Departments">
      <template #content>
        <span class="page-title">{{ department?.name || 'Department Details' }}</span>
      </template>
      <template #extra>
        <el-space v-if="isManagerOrAdmin && department">
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
          <el-button type="primary" @click="fetchDepartment">Retry</el-button>
          <el-button @click="handleBack">Back to List</el-button>
        </el-empty>
      </el-card>

      <!-- Content -->
      <template v-else-if="department">
        <!-- Basic Information -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <span class="card-title">Basic Information</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Name">{{ department.name }}</el-descriptions-item>
            <el-descriptions-item label="Code">{{ department.code }}</el-descriptions-item>
            <el-descriptions-item label="Description" :span="2">
              {{ department.description || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Status">
              <el-tag :type="department.is_active ? 'success' : 'info'" size="small">
                {{ department.is_active ? 'Active' : 'Inactive' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Created At">
              {{ formatDate(department.created_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- Relationships -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <span class="card-title">Relationships</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="Manager">
              <span 
                v-if="department.manager" 
                class="clickable-link" 
                @click="navigateToEmployee(department.manager.id)"
              >
                {{ department.manager.first_name }} {{ department.manager.last_name }}
              </span>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="Parent Department">
              <span 
                v-if="department.parent" 
                class="clickable-link" 
                @click="navigateToDepartment(department.parent.id)"
              >
                {{ department.parent.name }} ({{ department.parent.code }})
              </span>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="Child Departments">
              <div v-if="department.children && department.children.length > 0">
                <el-tag
                  v-for="child in department.children"
                  :key="child.id"
                  class="child-tag clickable-link"
                  @click="navigateToDepartment(child.id)"
                >
                  {{ child.name }} ({{ child.code }})
                </el-tag>
              </div>
              <span v-else>No child departments</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- Employees -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <span class="card-title">Employees</span>
          </template>
          <el-table 
            v-loading="loadingEmployees" 
            :data="employees" 
            stripe 
            style="width: 100%"
          >
            <el-table-column prop="employee_number" label="Employee #" width="120" />
            <el-table-column label="Name" min-width="150">
              <template #default="{ row }">
                <span 
                  class="clickable-link" 
                  @click="navigateToEmployee(row.id)"
                >
                  {{ row.first_name }} {{ row.last_name }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="email" label="Email" min-width="200" />
            <el-table-column label="Position" min-width="150">
              <template #default="{ row }">
                {{ row.position?.name || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="Hire Date" width="120">
              <template #default="{ row }">
                {{ row.hire_date ? new Date(row.hire_date).toLocaleDateString() : '-' }}
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="No employees in this department" />
            </template>
          </el-table>
        </el-card>
      </template>
    </div>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="editDialogVisible"
      title="Edit Department"
      width="600px"
      @close="formRef?.resetForm()"
    >
      <DepartmentForm
        ref="formRef"
        :model-value="department"
        @submit="handleEditSubmit"
      />
      <template #footer>
        <el-button @click="editDialogVisible = false">Cancel</el-button>
        <el-button
          type="primary"
          :loading="submittingEdit"
          @click="formRef?.handleSubmit()"
        >
          Save Changes
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'
import { getDepartment, deleteDepartment, updateDepartment, getDepartmentEmployees } from '@/api/departments'
import type { DepartmentEmployee } from '@/api/departments'
import { useAuth } from '@/composables/useAuth'
import type { Department, DepartmentUpdate } from '@/types/department'
import DepartmentForm from '@/components/DepartmentForm.vue'

defineOptions({
  name: 'DepartmentDetailPage',
})

const route = useRoute()
const router = useRouter()
const { isManagerOrAdmin } = useAuth()

const loading = ref(false)
const error = ref<string | null>(null)
const department = ref<Department | null>(null)

// Edit dialog state
const editDialogVisible = ref(false)
const formRef = ref<InstanceType<typeof DepartmentForm> | null>(null)
const submittingEdit = ref(false)

// Employees state
const employees = ref<DepartmentEmployee[]>([])
const loadingEmployees = ref(false)

const fetchDepartment = async () => {
  const id = route.params.id as string
  if (!id) {
    error.value = 'Invalid department ID'
    return
  }

  loading.value = true
  error.value = null

  try {
    const response = await getDepartment(id)
    department.value = response.data
    // Fetch employees after department is loaded
    await fetchEmployees()
  } catch (err) {
    console.error('Failed to fetch department:', err)
    const errorResponse = err as { response?: { status?: number } }
    if (errorResponse.response?.status === 404) {
      error.value = 'Department not found'
    } else {
      error.value = 'Failed to load department details'
    }
  } finally {
    loading.value = false
  }
}

const fetchEmployees = async () => {
  const id = route.params.id as string
  if (!id) return

  loadingEmployees.value = true
  try {
    const response = await getDepartmentEmployees(id)
    employees.value = response.data || []
  } catch (err) {
    console.error('Failed to fetch employees:', err)
    // Don't show error message, just keep empty list
    employees.value = []
  } finally {
    loadingEmployees.value = false
  }
}

const handleBack = () => {
  router.push({ name: 'Departments' })
}

const handleEdit = () => {
  editDialogVisible.value = true
}

const handleEditSubmit = async (payload: DepartmentUpdate) => {
  if (!department.value) return

  submittingEdit.value = true
  try {
    const response = await updateDepartment(department.value.id, payload)
    department.value = response.data
    editDialogVisible.value = false
    ElMessage.success('Department updated successfully')
  } catch (err) {
    console.error('Failed to update department:', err)
    ElMessage.error('Failed to update department')
  } finally {
    submittingEdit.value = false
  }
}

const handleDelete = async () => {
  if (!department.value) return

  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete the department "${department.value.name}"?`,
      'Confirm Delete',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
      }
    )

    loading.value = true
    await deleteDepartment(department.value.id)
    ElMessage.success('Department deleted successfully')
    router.push({ name: 'Departments' })
  } catch (err) {
    if (err !== 'cancel') {
      console.error('Failed to delete department:', err)
      ElMessage.error('Failed to delete department')
    }
  } finally {
    loading.value = false
  }
}

const navigateToEmployee = (id: string) => {
  router.push({ name: 'EmployeeDetail', params: { id } })
}

const navigateToDepartment = (id: string) => {
  router.push({ name: 'DepartmentDetail', params: { id } })
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString()
}

// Watch for route parameter changes to refetch data when navigating between departments
watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      fetchDepartment()
    }
  }
)

onMounted(() => {
  fetchDepartment()
})
</script>

<style scoped>
.department-detail {
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
  cursor: pointer;
  color: #409eff;
  transition: color 0.3s;
}

.clickable-link:hover {
  color: #66b1ff;
  text-decoration: underline;
}

.child-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}
</style>
