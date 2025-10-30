<template>
  <div class="roles-list">
    <div class="page-header">
      <h1>Roles</h1>
      <el-button v-if="isManagerOrAdmin" type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        Add Role
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
        <el-form-item label="Type">
          <el-select 
            v-model="systemRoleFilter" 
            placeholder="All" 
            style="width: 150px"
            clearable
            @change="handleFilterChange"
          >
            <el-option label="System Roles" :value="true" />
            <el-option label="Custom Roles" :value="false" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Roles Table -->
    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="roles"
        style="width: 100%"
        stripe
        class="roles-table"
      >
        <el-table-column prop="name" label="Name" min-width="150" fixed>
          <template #default="{ row }">
            <span class="clickable-link" @click="navigateToRole(row.id)">
              {{ row.name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="Code" width="150" />
        <el-table-column prop="description" label="Description" min-width="200" show-overflow-tooltip />
        <el-table-column label="Type" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_system_role" type="info" size="small">System</el-tag>
            <el-tag v-else type="success" size="small">Custom</el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="isManagerOrAdmin" label="Actions" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button 
              v-if="!row.is_system_role" 
              size="small" 
              type="danger" 
              @click="handleDelete(row)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="No roles found" />
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

    <!-- Create/Edit Role Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? 'Create Role' : 'Edit Role'"
      width="600px"
      :close-on-click-modal="false"
      @closed="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="Name" prop="name">
          <el-input
            v-model="form.name"
            placeholder="e.g., Custom Manager"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="Code" prop="code">
          <el-input
            v-model="form.code"
            placeholder="e.g., CUSTOM_MANAGER"
            maxlength="50"
            show-word-limit
            :disabled="dialogMode === 'edit'"
          >
            <template v-if="dialogMode === 'edit'" #suffix>
              <el-tooltip content="Role code cannot be changed after creation">
                <el-icon><InfoFilled /></el-icon>
              </el-tooltip>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="Description" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="Describe the purpose of this role"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" :disabled="submitting">Cancel</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ dialogMode === 'create' ? 'Create' : 'Update' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, Edit, Delete, InfoFilled } from '@element-plus/icons-vue'
import { useAuth } from '@/composables/useAuth'
import { getRoles, createRole, updateRole, deleteRole } from '@/api/roles'
import type { Role, RoleCreate, RoleUpdate } from '@/types/role'

defineOptions({
  name: 'RolesListPage',
})

const { isManagerOrAdmin } = useAuth()
const router = useRouter()

// State
const loading = ref(false)
const submitting = ref(false)
const roles = ref<Role[]>([])
const searchQuery = ref('')
const systemRoleFilter = ref<boolean | undefined>(undefined)

// Dialog state
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentRole = ref<Role | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({
  name: '',
  code: '',
  description: '',
})

// Pagination
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

// Form validation rules
const rules: FormRules = {
  name: [
    { required: true, message: 'Please enter role name', trigger: 'blur' },
    { min: 1, max: 100, message: 'Name must be between 1 and 100 characters', trigger: 'blur' },
  ],
  code: [
    { required: true, message: 'Please enter role code', trigger: 'blur' },
    { min: 1, max: 50, message: 'Code must be between 1 and 50 characters', trigger: 'blur' },
    { 
      pattern: /^[A-Z0-9_]+$/, 
      message: 'Code must be uppercase letters, numbers, and underscores only', 
      trigger: 'blur',
    },
  ],
  description: [
    { max: 500, message: 'Description cannot exceed 500 characters', trigger: 'blur' },
  ],
}

// Lifecycle
onMounted(() => {
  loadRoles()
})

// Methods
const loadRoles = async () => {
  try {
    loading.value = true
    const response = await getRoles({
      page: pagination.page,
      page_size: pagination.pageSize,
      is_system_role: systemRoleFilter.value ?? undefined,
      search: searchQuery.value || undefined,
    })

    if (response.status === 200 && response.data) {
      roles.value = response.data.data
      pagination.total = response.data.total
    }
  } catch (error) {
    console.error('Error loading roles:', error)
    ElMessage.error('Failed to load roles')
  } finally {
    loading.value = false
  }
}

// Search with debounce
let searchTimeout: ReturnType<typeof setTimeout>
const handleSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    pagination.page = 1
    loadRoles()
  }, 300)
}

// Filter handler
const handleFilterChange = () => {
  pagination.page = 1
  loadRoles()
}

// Pagination handlers
const handlePageChange = () => {
  loadRoles()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadRoles()
}

// CRUD handlers
const handleCreate = () => {
  dialogMode.value = 'create'
  currentRole.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (role: Role) => {
  dialogMode.value = 'edit'
  currentRole.value = role
  form.name = role.name
  form.code = role.code
  form.description = role.description || ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (dialogMode.value === 'create') {
      const data: RoleCreate = {
        name: form.name,
        code: form.code,
        description: form.description || null,
      }
      await createRole(data)
      ElMessage.success('Role created successfully')
    } else {
      if (!currentRole.value) return
      const data: RoleUpdate = {
        name: form.name,
        description: form.description || null,
      }
      await updateRole(currentRole.value.id, data)
      ElMessage.success('Role updated successfully')
    }

    dialogVisible.value = false
    loadRoles()
  } catch (error) {
    console.error('Error submitting role:', error)
    const err = error as { response?: { data?: { detail?: string } } }
    const errorMessage = err?.response?.data?.detail || `Failed to ${dialogMode.value} role`
    ElMessage.error(errorMessage)
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (role: Role) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete role "${role.name}"?`,
      'Delete Confirmation',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
      }
    )

    await deleteRole(role.id)
    ElMessage.success('Role deleted successfully')
    loadRoles()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Error deleting role:', error)
      const err = error as { response?: { data?: { detail?: string } } }
      const errorMessage = err?.response?.data?.detail || 'Failed to delete role'
      ElMessage.error(errorMessage)
    }
  }
}

const handleDialogClose = () => {
  resetForm()
  currentRole.value = null
}

const resetForm = () => {
  form.name = ''
  form.code = ''
  form.description = ''
  formRef.value?.clearValidate()
}

// Navigation handler
const navigateToRole = (id: string) => {
  router.push({ name: 'RoleDetail', params: { id } })
}
</script>

<style scoped>
.roles-list {
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
  .roles-list {
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
