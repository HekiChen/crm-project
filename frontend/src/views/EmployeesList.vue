<template>
  <div class="employees-list">
    <div class="page-header">
      <h1>Employees</h1>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        Add Employee
      </el-button>
    </div>

    <!-- Search and Filters -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true">
        <el-form-item label="Search">
          <el-input
            v-model="searchQuery"
            placeholder="Search by name, email, or employee #"
            clearable
            style="width: 280px"
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="Position">
          <el-select 
            v-model="positionFilter" 
            placeholder="All Positions" 
            clearable
            style="width: 180px"
            @change="loadEmployees"
          >
            <el-option
              v-for="position in positions"
              :key="position.id"
              :label="position.name"
              :value="position.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Department">
          <el-select 
            v-model="departmentFilter" 
            placeholder="All Departments" 
            clearable
            style="width: 180px"
            @change="loadEmployees"
          >
            <el-option
              v-for="department in departments"
              :key="department.id"
              :label="department.name"
              :value="department.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Status">
          <el-select 
            v-model="statusFilter" 
            placeholder="All" 
            style="width: 120px"
            @change="loadEmployees"
          >
            <el-option label="All" :value="null" />
            <el-option label="Active" :value="true" />
            <el-option label="Inactive" :value="false" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Employees Table -->
    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="employees"
        style="width: 100%"
        stripe
        class="employees-table"
      >
        <el-table-column prop="employee_number" label="Employee #" width="120" fixed />
        <el-table-column label="Name" min-width="150">
          <template #default="{ row }">
            <span class="clickable-link" @click="navigateToEmployee(row.id)">
              {{ row.first_name }} {{ row.last_name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="Email" min-width="200" show-overflow-tooltip />
        <el-table-column label="Position" width="180" class-name="hide-on-mobile">
          <template #default="{ row }">
            <span v-if="row.position">{{ row.position.name }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="Department" width="150" class-name="hide-on-mobile">
          <template #default="{ row }">
            <span v-if="row.department">{{ row.department.name }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="Manager" width="150" class-name="hide-on-mobile">
          <template #default="{ row }">
            <span 
              v-if="row.manager" 
              class="clickable-link" 
              @click="navigateToEmployee(row.manager.id)"
            >
              {{ row.manager.first_name }} {{ row.manager.last_name }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="Hire Date" width="120" class-name="hide-on-mobile">
          <template #default="{ row }">
            {{ formatDate(row.hire_date) }}
          </template>
        </el-table-column>
        <el-table-column label="Status" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? 'Active' : 'Inactive' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">
              <el-icon><View /></el-icon>
            </el-button>
            <el-button size="small" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="No employees found" />
        </template>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- Create/Edit Employee Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? 'Edit Employee' : 'Create Employee'"
      width="700px"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <EmployeeForm
        ref="employeeFormRef"
        :model-value="currentEmployee"
        :positions="positions"
        :departments="departments"
        :active-employees="activeEmployees"
        @submit="handleFormSubmit"
      />

      <template #footer>
        <el-button @click="dialogVisible = false" :disabled="submitting">Cancel</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ isEditMode ? 'Update' : 'Create' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, View, Edit, Delete } from '@element-plus/icons-vue'
import EmployeeForm from '@/components/EmployeeForm.vue'
import { 
  getEmployees, 
  createEmployee, 
  updateEmployee, 
  deleteEmployee 
} from '@/api/employees'
import { getPositions } from '@/api/positions'
import { getDepartments } from '@/api/departments'
import type { Employee, EmployeeCreate, EmployeeUpdate } from '@/types/employee'
import type { Position } from '@/types/position'
import type { Department } from '@/types/department'

defineOptions({
  name: 'EmployeesListPage',
})

const router = useRouter()

// State
const loading = ref(false)
const submitting = ref(false)
const employees = ref<Employee[]>([])
const positions = ref<Position[]>([])
const departments = ref<Department[]>([])
const activeEmployees = ref<Employee[]>([])
const searchQuery = ref('')
const positionFilter = ref<string | null>(null)
const departmentFilter = ref<string | null>(null)
const statusFilter = ref<boolean | null>(null)

// Dialog state
const dialogVisible = ref(false)
const isEditMode = ref(false)
const currentEmployee = ref<Employee | null>(null)
const employeeFormRef = ref<InstanceType<typeof EmployeeForm>>()

// Pagination
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

// Lifecycle
onMounted(() => {
  loadEmployees()
  loadPositions()
  loadDepartments()
  loadActiveEmployees()
})

// Methods
const loadEmployees = async () => {
  try {
    loading.value = true
    const response = await getEmployees({
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchQuery.value || undefined,
      position_id: positionFilter.value || undefined,
      department_id: departmentFilter.value || undefined,
      is_active: statusFilter.value ?? undefined,
    })

    if (response.data) {
      employees.value = response.data.data
      pagination.total = response.data.total
    }
  } catch (error) {
    console.error('Error loading employees:', error)
    ElMessage.error('Failed to load employees')
  } finally {
    loading.value = false
  }
}

const loadPositions = async () => {
  try {
    const response = await getPositions({ page: 1, page_size: 1000 })
    if (response.data) {
      positions.value = response.data.data
    }
  } catch (error) {
    console.error('Error loading positions:', error)
  }
}

const loadDepartments = async () => {
  try {
    const response = await getDepartments({ page: 1, page_size: 1000 })
    if (response.data) {
      departments.value = response.data.data
    }
  } catch (error) {
    console.error('Error loading departments:', error)
  }
}

const loadActiveEmployees = async () => {
  try {
    const response = await getEmployees({ page: 1, page_size: 1000, is_active: true })
    if (response.data) {
      activeEmployees.value = response.data.data
    }
  } catch (error) {
    console.error('Error loading active employees:', error)
  }
}

// Search with debounce
let searchTimeout: ReturnType<typeof setTimeout>
const handleSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    pagination.page = 1
    loadEmployees()
  }, 300)
}

// Pagination handlers
const handleSizeChange = () => {
  pagination.page = 1
  loadEmployees()
}

const handlePageChange = () => {
  loadEmployees()
}

// Navigation
const navigateToEmployee = (id: string) => {
  router.push(`/employees/${id}`)
}

// CRUD handlers
const handleCreate = () => {
  isEditMode.value = false
  currentEmployee.value = null
  dialogVisible.value = true
}

const handleView = (employee: Employee) => {
  navigateToEmployee(employee.id)
}

const handleEdit = (employee: Employee) => {
  isEditMode.value = true
  currentEmployee.value = employee
  dialogVisible.value = true
}

const handleDelete = (employee: Employee) => {
  ElMessageBox.confirm(
    `Are you sure you want to delete employee "${employee.first_name} ${employee.last_name}"? This action will mark the employee as inactive.`,
    'Confirm Delete',
    {
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await deleteEmployee(employee.id)
        ElMessage.success('Employee deleted successfully')
        loadEmployees()
      } catch (error) {
        console.error('Error deleting employee:', error)
        ElMessage.error('Failed to delete employee')
      }
    })
    .catch(() => {
      // User cancelled
    })
}

const handleSubmit = async () => {
  // Trigger validation and submission in the child form component
  employeeFormRef.value?.handleSubmit()
}

const handleFormSubmit = async (formData: EmployeeCreate | EmployeeUpdate) => {
  try {
    submitting.value = true

    if (isEditMode.value && currentEmployee.value) {
      // Update existing employee
      await updateEmployee(currentEmployee.value.id, formData as EmployeeUpdate)
      ElMessage.success('Employee updated successfully')
    } else {
      // Create new employee
      await createEmployee(formData as EmployeeCreate)
      ElMessage.success('Employee created successfully')
    }

    dialogVisible.value = false
    loadEmployees()
    loadActiveEmployees() // Refresh for manager dropdown
  } catch (error: any) {
    console.error('Error saving employee:', error)
    const message = error.response?.data?.detail || 'Failed to save employee'
    ElMessage.error(message)
  } finally {
    submitting.value = false
  }
}

const handleDialogClosed = () => {
  currentEmployee.value = null
  employeeFormRef.value?.resetForm()
}

// Utility functions
const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.employees-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.filter-card {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding: 10px 0;
}

.clickable-link {
  color: var(--el-color-primary);
  cursor: pointer;
  text-decoration: none;
}

.clickable-link:hover {
  text-decoration: underline;
}

.text-muted {
  color: var(--el-text-color-secondary);
}

/* Responsive styles */
@media (max-width: 768px) {
  .hide-on-mobile {
    display: none !important;
  }

  .filter-card :deep(.el-form--inline .el-form-item) {
    display: block;
    margin-right: 0;
  }
}
</style>
