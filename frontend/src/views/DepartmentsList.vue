<template>
  <div class="departments-list">
    <div class="page-header">
      <h1>Departments</h1>
      <el-button v-if="isManagerOrAdmin" type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        Add Department
      </el-button>
    </div>

    <!-- Search and Filters -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true">
        <el-form-item label="Search">
          <el-input
            v-model="searchQuery"
            placeholder="Search by name or code"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="Status">
          <el-select 
            v-model="statusFilter" 
            placeholder="All" 
            style="width: 120px"
            @change="loadDepartments"
          >
            <el-option label="All" :value="null" />
            <el-option label="Active" :value="true" />
            <el-option label="Inactive" :value="false" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Departments Table -->
    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="departments"
        style="width: 100%"
        stripe
        class="departments-table"
      >
        <el-table-column prop="name" label="Name" min-width="150" fixed>
          <template #default="{ row }">
            <span class="clickable-link" @click="navigateToDepartment(row.id)">
              {{ row.name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="Code" width="120" />
        <el-table-column prop="description" label="Description" min-width="200" show-overflow-tooltip />
        <el-table-column label="Manager" width="150" class-name="hide-on-mobile">
          <template #default="{ row }">
            <span 
              v-if="row.manager" 
              class="clickable-link" 
              @click="navigateToEmployee(row.manager.id)"
            >
              {{ row.manager.first_name }} {{ row.manager.last_name }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="Parent" width="150" class-name="hide-on-mobile">
          <template #default="{ row }">
            <span 
              v-if="row.parent_id" 
              class="clickable-link" 
              @click="navigateToDepartment(row.parent_id)"
            >
              {{ departmentMap[row.parent_id] || row.parent_id }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="Status" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? 'Active' : 'Inactive' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="isManagerOrAdmin" label="Actions" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="No departments found" />
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

    <!-- Create Department Dialog -->
    <el-dialog
      v-model="createDialogVisible"
      title="Create Department"
      width="600px"
      :close-on-click-modal="false"
    >
      <DepartmentForm
        ref="departmentFormRef"
        @submit="handleCreateSubmit"
      />
      <template #footer>
        <el-button @click="createDialogVisible = false" :disabled="submitting">Cancel</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="departmentFormRef?.handleSubmit()"
        >
          Create
        </el-button>
      </template>
    </el-dialog>

    <!-- Edit Department Dialog -->
    <el-dialog
      v-model="editDialogVisible"
      title="Edit Department"
      width="600px"
      :close-on-click-modal="false"
      @closed="editingDepartment = null"
    >
      <DepartmentForm
        ref="departmentFormRef"
        :model-value="editingDepartment"
        @submit="handleEditSubmit"
      />
      <template #footer>
        <el-button @click="editDialogVisible = false" :disabled="submitting">Cancel</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="departmentFormRef?.handleSubmit()"
        >
          Update
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
import { useAuth } from '@/composables/useAuth'
import { getDepartments, deleteDepartment, createDepartment, updateDepartment } from '@/api/departments'
import type { Department, DepartmentCreate, DepartmentUpdate } from '@/types/department'
import DepartmentForm from '@/components/DepartmentForm.vue'

defineOptions({
  name: 'DepartmentsListPage',
})

const { isManagerOrAdmin } = useAuth()
const router = useRouter()

// State
const loading = ref(false)
const submitting = ref(false)
const departments = ref<Department[]>([])
const searchQuery = ref('')
const statusFilter = ref<boolean | null>(null)

// Dialog state
const createDialogVisible = ref(false)
const editDialogVisible = ref(false)
const departmentFormRef = ref<InstanceType<typeof DepartmentForm>>()
const editingDepartment = ref<Department | null>(null)

// Pagination
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

// Computed lookup for parent department names
const departmentMap = computed(() => {
  return departments.value.reduce((map, dept) => {
    map[dept.id] = dept.name
    return map
  }, {} as Record<string, string>)
})

// Lifecycle
onMounted(() => {
  loadDepartments()
})

// Methods
const loadDepartments = async () => {
  try {
    loading.value = true
    const response = await getDepartments({
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchQuery.value || undefined,
      is_active: statusFilter.value ?? undefined,
    })

    if (response.status === 200 && response.data) {
      departments.value = response.data.data
      pagination.total = response.data.total
    }
  } catch (error) {
    console.error('Error loading departments:', error)
    ElMessage.error('Failed to load departments')
  } finally {
    loading.value = false
  }
}

// Search with debounce
let searchTimeout: ReturnType<typeof setTimeout>
const handleSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    pagination.page = 1 // Reset to first page on search
    loadDepartments()
  }, 300)
}

// Pagination handlers
const handlePageChange = () => {
  loadDepartments()
}

const handleSizeChange = () => {
  pagination.page = 1 // Reset to first page when size changes
  loadDepartments()
}

// CRUD handlers
const handleCreate = () => {
  createDialogVisible.value = true
}

const handleCreateSubmit = async (data: DepartmentCreate | DepartmentUpdate) => {
  try {
    submitting.value = true
    await createDepartment(data as DepartmentCreate)
    ElMessage.success('Department created successfully')
    createDialogVisible.value = false
    departmentFormRef.value?.resetForm()
    loadDepartments()
  } catch (error) {
    console.error('Error creating department:', error)
    ElMessage.error('Failed to create department')
  } finally {
    submitting.value = false
  }
}

const handleEdit = (department: Department) => {
  editingDepartment.value = department
  editDialogVisible.value = true
}

const handleEditSubmit = async (data: DepartmentCreate | DepartmentUpdate) => {
  if (!editingDepartment.value) return

  try {
    submitting.value = true
    await updateDepartment(editingDepartment.value.id, data as DepartmentUpdate)
    ElMessage.success('Department updated successfully')
    editDialogVisible.value = false
    editingDepartment.value = null
    loadDepartments()
  } catch (error) {
    console.error('Error updating department:', error)
    ElMessage.error('Failed to update department')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (department: Department) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete department "${department.name}"?`,
      'Delete Confirmation',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
      }
    )

    await deleteDepartment(department.id)
    ElMessage.success('Department deleted successfully')
    loadDepartments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Error deleting department:', error)
      ElMessage.error('Failed to delete department')
    }
  }
}

// Navigation handlers
const navigateToDepartment = (id: string) => {
  router.push({ name: 'DepartmentDetail', params: { id } })
}

const navigateToEmployee = (id: string) => {
  router.push({ name: 'EmployeeDetail', params: { id } })
}
</script>

<style scoped>
.departments-list {
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
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
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

/* Responsive styles */
@media screen and (max-width: 768px) {
  .departments-list {
    padding: 10px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .page-header h1 {
    font-size: 20px;
  }

  .filter-card :deep(.el-form) {
    display: flex;
    flex-direction: column;
  }

  .filter-card :deep(.el-form-item) {
    width: 100%;
    margin-right: 0;
  }

  .pagination-container {
    justify-content: center;
  }

  .pagination-container :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
  }

  /* Hide manager and parent columns on mobile */
  .departments-table :deep(.hide-on-mobile) {
    display: none;
  }
}

@media screen and (max-width: 480px) {
  .page-header h1 {
    font-size: 18px;
  }

  /* Stack dialog buttons on small screens */
  :deep(.el-dialog__footer) {
    display: flex;
    flex-direction: column-reverse;
    gap: 10px;
  }

  :deep(.el-dialog__footer .el-button) {
    width: 100%;
    margin: 0;
  }
}
</style>
