<template>
  <div class="role-detail">
    <el-page-header @back="handleBack" title="Back to Roles">
      <template #content>
        <span class="page-title">{{ role?.name || 'Role Details' }}</span>
      </template>
      <template #extra>
        <el-space v-if="isManagerOrAdmin && role">
          <el-button @click="handleEdit">
            <el-icon><Edit /></el-icon>
            Edit
          </el-button>
          <el-button v-if="!role.is_system_role" type="danger" @click="handleDelete">
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
          <el-button type="primary" @click="fetchRole">Retry</el-button>
          <el-button @click="handleBack">Back to List</el-button>
        </el-empty>
      </el-card>

      <!-- Content -->
      <template v-else-if="role">
        <!-- Basic Information -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <span class="card-title">Basic Information</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Name">{{ role.name }}</el-descriptions-item>
            <el-descriptions-item label="Code">{{ role.code }}</el-descriptions-item>
            <el-descriptions-item label="Description" :span="2">
              {{ role.description || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Type">
              <el-tag v-if="role.is_system_role" type="info" size="small">System Role</el-tag>
              <el-tag v-else type="success" size="small">Custom Role</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Created At">
              {{ formatDate(role.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="Updated At" :span="2">
              {{ formatDate(role.updated_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- Assigned Employees -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">Assigned Employees</span>
              <el-tag type="info" size="small">{{ employees.length }} Total</el-tag>
            </div>
          </template>
          <div v-loading="employeesLoading">
            <el-table
              v-if="employees.length > 0"
              :data="employees"
              style="width: 100%"
            >
              <el-table-column prop="employee_name" label="Name" min-width="120" />
              <el-table-column prop="email" label="Email" min-width="150" />
              <el-table-column prop="position" label="Position" min-width="120">
                <template #default="{ row }">
                  {{ row.position || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="department" label="Department" min-width="120">
                <template #default="{ row }">
                  {{ row.department || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="assigned_at" label="Assigned Date" min-width="140">
                <template #default="{ row }">
                  {{ formatDate(row.assigned_at) }}
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="No employees assigned to this role" :image-size="80" />
          </div>
        </el-card>

        <!-- Menu Permissions -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">Menu Permissions</span>
              <el-tag type="info" size="small">{{ permissions.length }} Total</el-tag>
            </div>
          </template>
          <div v-loading="permissionsLoading">
            <el-table
              v-if="permissions.length > 0"
              :data="permissions"
              style="width: 100%"
            >
              <el-table-column prop="menu_name" label="Menu" min-width="150" />
              <el-table-column prop="menu_path" label="Path" min-width="150" />
              <el-table-column prop="menu_type" label="Type" width="100">
                <template #default="{ row }">
                  <el-tag :type="getMenuTypeTagType(row.menu_type)" size="small">
                    {{ row.menu_type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="Permissions" min-width="200">
                <template #default="{ row }">
                  <el-space :size="5" wrap>
                    <el-tag v-if="row.can_read" type="success" size="small">Read</el-tag>
                    <el-tag v-if="row.can_write" type="warning" size="small">Write</el-tag>
                    <el-tag v-if="row.can_delete" type="danger" size="small">Delete</el-tag>
                  </el-space>
                </template>
              </el-table-column>
              <el-table-column v-if="isManagerOrAdmin && !role?.is_system_role" label="Actions" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" @click="handleEditPermission(row)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="No permissions assigned to this role" :image-size="80" />
          </div>
        </el-card>
      </template>
    </div>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="editDialogVisible"
      title="Edit Role"
      width="600px"
      :close-on-click-modal="false"
      @closed="handleEditDialogClose"
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
            disabled
          >
            <template #suffix>
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
        <el-button @click="editDialogVisible = false" :disabled="submitting">Cancel</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleEditSubmit"
        >
          Update
        </el-button>
      </template>
    </el-dialog>

    <!-- Edit Permission Dialog -->
    <el-dialog
      v-model="permissionDialogVisible"
      title="Edit Menu Permission"
      width="500px"
      :close-on-click-modal="false"
      @closed="handlePermissionDialogClose"
    >
      <el-form
        v-if="currentPermission"
        label-width="120px"
      >
        <el-form-item label="Menu">
          <el-input :value="currentPermission.menu_name" disabled />
        </el-form-item>
        <el-form-item label="Path">
          <el-input :value="currentPermission.menu_path" disabled />
        </el-form-item>
        <el-form-item label="Permissions">
          <el-space direction="vertical" style="width: 100%">
            <el-checkbox v-model="permissionForm.can_read">
              <el-tag type="success" size="small">Read</el-tag>
              <span style="margin-left: 8px">View this menu/page</span>
            </el-checkbox>
            <el-checkbox v-model="permissionForm.can_write">
              <el-tag type="warning" size="small">Write</el-tag>
              <span style="margin-left: 8px">Create and update records</span>
            </el-checkbox>
            <el-checkbox v-model="permissionForm.can_delete">
              <el-tag type="danger" size="small">Delete</el-tag>
              <span style="margin-left: 8px">Delete records</span>
            </el-checkbox>
          </el-space>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="permissionDialogVisible = false" :disabled="submitting">Cancel</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handlePermissionSubmit"
        >
          Update Permission
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Edit, Delete, InfoFilled } from '@element-plus/icons-vue'
import { getRole, updateRole, deleteRole, getRoleEmployees, getRolePermissions, updateRolePermission } from '@/api/roles'
import { useAuth } from '@/composables/useAuth'
import type { Role, RoleUpdate, RoleEmployee, RolePermission } from '@/types/role'

defineOptions({
  name: 'RoleDetailPage',
})

const route = useRoute()
const router = useRouter()
const { isManagerOrAdmin } = useAuth()

const loading = ref(false)
const submitting = ref(false)
const error = ref<string | null>(null)
const role = ref<Role | null>(null)

// Employees and permissions
const employees = ref<RoleEmployee[]>([])
const permissions = ref<RolePermission[]>([])
const employeesLoading = ref(false)
const permissionsLoading = ref(false)

// Edit dialog state
const editDialogVisible = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({
  name: '',
  code: '',
  description: '',
})

// Permission dialog state
const permissionDialogVisible = ref(false)
const currentPermission = ref<RolePermission | null>(null)
const permissionForm = reactive({
  can_read: false,
  can_write: false,
  can_delete: false,
})

// Form validation rules
const rules: FormRules = {
  name: [
    { required: true, message: 'Please enter role name', trigger: 'blur' },
    { min: 1, max: 100, message: 'Name must be between 1 and 100 characters', trigger: 'blur' },
  ],
  description: [
    { max: 500, message: 'Description cannot exceed 500 characters', trigger: 'blur' },
  ],
}

const fetchRole = async () => {
  const id = route.params.id as string
  if (!id) {
    error.value = 'Invalid role ID'
    return
  }

  loading.value = true
  error.value = null

  try {
    const response = await getRole(id)
    role.value = response.data
    // Fetch employees and permissions in parallel
    await Promise.all([
      fetchEmployees(id),
      fetchPermissions(id)
    ])
  } catch (err) {
    console.error('Failed to fetch role:', err)
    const errorResponse = err as { response?: { status?: number } }
    if (errorResponse.response?.status === 404) {
      error.value = 'Role not found'
    } else {
      error.value = 'Failed to load role details'
    }
  } finally {
    loading.value = false
  }
}

const fetchEmployees = async (roleId: string) => {
  employeesLoading.value = true
  try {
    const response = await getRoleEmployees(roleId)
    employees.value = response.data || []
  } catch (err) {
    console.error('Failed to fetch employees:', err)
    ElMessage.warning('Failed to load assigned employees')
    employees.value = []
  } finally {
    employeesLoading.value = false
  }
}

const fetchPermissions = async (roleId: string) => {
  permissionsLoading.value = true
  try {
    const response = await getRolePermissions(roleId)
    permissions.value = response.data || []
  } catch (err) {
    console.error('Failed to fetch permissions:', err)
    ElMessage.warning('Failed to load menu permissions')
    permissions.value = []
  } finally {
    permissionsLoading.value = false
  }
}

const getMenuTypeTagType = (menuType?: string): 'success' | 'info' | 'warning' | 'danger' => {
  if (!menuType) return 'info'
  const typeMap: Record<string, 'success' | 'info' | 'warning' | 'danger'> = {
    'menu': 'success',
    'page': 'info',
    'button': 'warning',
    'action': 'danger',
  }
  return typeMap[menuType.toLowerCase()] || 'info'
}

const handleBack = () => {
  router.push({ name: 'Roles' })
}

const handleEdit = () => {
  if (!role.value) return
  
  form.name = role.value.name
  form.code = role.value.code
  form.description = role.value.description || ''
  editDialogVisible.value = true
}

const handleEditSubmit = async () => {
  if (!formRef.value || !role.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    const data: RoleUpdate = {
      name: form.name,
      description: form.description || null,
    }
    await updateRole(role.value.id, data)
    ElMessage.success('Role updated successfully')
    editDialogVisible.value = false
    await fetchRole()
  } catch (error) {
    console.error('Error updating role:', error)
    const err = error as { response?: { data?: { detail?: string } } }
    const errorMessage = err?.response?.data?.detail || 'Failed to update role'
    ElMessage.error(errorMessage)
  } finally {
    submitting.value = false
  }
}

const handleEditDialogClose = () => {
  form.name = ''
  form.code = ''
  form.description = ''
  formRef.value?.clearValidate()
}

const handleEditPermission = (permission: RolePermission) => {
  currentPermission.value = permission
  permissionForm.can_read = permission.can_read
  permissionForm.can_write = permission.can_write
  permissionForm.can_delete = permission.can_delete
  permissionDialogVisible.value = true
}

const handlePermissionSubmit = async () => {
  if (!currentPermission.value || !role.value) return

  try {
    submitting.value = true
    
    await updateRolePermission(
      role.value.id,
      currentPermission.value.menu_id,
      {
        can_read: permissionForm.can_read,
        can_write: permissionForm.can_write,
        can_delete: permissionForm.can_delete,
      }
    )
    
    ElMessage.success('Permission updated successfully')
    permissionDialogVisible.value = false
    
    // Refresh permissions
    await fetchPermissions(role.value.id)
  } catch (error) {
    console.error('Error updating permission:', error)
    const err = error as { response?: { data?: { detail?: string } } }
    const errorMessage = err?.response?.data?.detail || 'Failed to update permission'
    ElMessage.error(errorMessage)
  } finally {
    submitting.value = false
  }
}

const handlePermissionDialogClose = () => {
  currentPermission.value = null
  permissionForm.can_read = false
  permissionForm.can_write = false
  permissionForm.can_delete = false
}

const handleDelete = async () => {
  if (!role.value) return

  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete the role "${role.value.name}"?`,
      'Confirm Delete',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
      }
    )

    loading.value = true
    await deleteRole(role.value.id)
    ElMessage.success('Role deleted successfully')
    router.push({ name: 'Roles' })
  } catch (err) {
    if (err !== 'cancel') {
      console.error('Failed to delete role:', err)
      const error = err as { response?: { data?: { detail?: string } } }
      const errorMessage = error?.response?.data?.detail || 'Failed to delete role'
      ElMessage.error(errorMessage)
    }
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString()
}

// Watch for route parameter changes to refetch data when navigating between roles
watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      fetchRole()
    }
  }
)

onMounted(() => {
  fetchRole()
})
</script>

<style scoped>
.role-detail {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

/* Responsive styles */
@media screen and (max-width: 768px) {
  .role-detail {
    padding: 10px;
  }

  .page-title {
    font-size: 18px;
  }
}

@media screen and (max-width: 480px) {
  .page-title {
    font-size: 16px;
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
