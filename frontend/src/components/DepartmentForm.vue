<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-width="120px"
    @submit.prevent="handleSubmit"
  >
    <el-form-item label="Name" prop="name">
      <el-input v-model="formData.name" placeholder="Enter department name" />
    </el-form-item>

    <el-form-item label="Code" prop="code">
      <el-input 
        v-model="formData.code" 
        :disabled="isEditing"
        placeholder="Enter department code" 
      />
    </el-form-item>

    <el-form-item label="Description" prop="description">
      <el-input
        v-model="formData.description"
        type="textarea"
        :rows="3"
        placeholder="Enter department description"
      />
    </el-form-item>

    <el-form-item label="Parent Department" prop="parent_id">
      <el-select
        v-model="formData.parent_id"
        placeholder="Select parent department (optional)"
        clearable
        filterable
        style="width: 100%"
      >
        <el-option
          v-for="dept in parentOptions"
          :key="dept.id"
          :label="dept.name"
          :value="dept.id"
        />
      </el-select>
    </el-form-item>

    <el-form-item label="Manager" prop="manager_id">
      <el-select
        v-model="formData.manager_id"
        placeholder="Select manager (optional)"
        clearable
        filterable
        style="width: 100%"
        :loading="loadingEmployees"
      >
        <el-option
          v-for="emp in availableEmployees"
          :key="emp.id"
          :label="`${emp.first_name} ${emp.last_name} (${emp.employee_number})`"
          :value="emp.id"
        />
      </el-select>
    </el-form-item>

    <el-form-item label="Status" prop="is_active">
      <el-switch
        v-model="formData.is_active"
        active-text="Active"
        inactive-text="Inactive"
      />
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, computed } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { Department, DepartmentCreate, DepartmentUpdate } from '@/types/department'
import type { Employee } from '@/types/employee'
import { getDepartments } from '@/api/departments'
import { getEmployees } from '@/api/employees'

interface Props {
  modelValue?: Department | null
  excludeIds?: string[]
}

interface Emits {
  (e: 'submit', data: DepartmentCreate | DepartmentUpdate): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  excludeIds: () => [],
})

const emit = defineEmits<Emits>()

// Form ref
const formRef = ref<FormInstance>()

// Form data
const formData = reactive<DepartmentCreate & { is_active: boolean }>({
  name: '',
  code: '',
  description: '',
  parent_id: undefined,
  manager_id: undefined,
  is_active: true,
})

// Available parent departments
const availableParents = ref<Department[]>([])

// Available employees for manager selection
const availableEmployees = ref<Employee[]>([])
const loadingEmployees = ref(false)

// Computed: Check if form is in edit mode
const isEditing = computed(() => !!props.modelValue)

// Computed parent options (exclude current department and its descendants if editing)
const parentOptions = computed(() => {
  let options = availableParents.value
  
  // If editing, exclude the current department and its children
  if (props.modelValue) {
    options = options.filter(dept => 
      dept.id !== props.modelValue!.id && 
      !props.excludeIds.includes(dept.id)
    )
  }
  
  return options
})

// Validation rules
const rules: FormRules = {
  name: [
    { required: true, message: 'Please enter department name', trigger: 'blur' },
    { min: 2, max: 100, message: 'Name must be between 2 and 100 characters', trigger: 'blur' },
  ],
  code: [
    { required: true, message: 'Please enter department code', trigger: 'blur' },
    { min: 2, max: 50, message: 'Code must be between 2 and 50 characters', trigger: 'blur' },
    { 
      pattern: /^[A-Z0-9_-]+$/i, 
      message: 'Code can only contain letters, numbers, underscores, and hyphens', 
      trigger: 'blur' 
    },
  ],
  description: [
    { max: 500, message: 'Description cannot exceed 500 characters', trigger: 'blur' },
  ],
}

// Methods
const resetForm = () => {
  formData.name = ''
  formData.code = ''
  formData.description = ''
  formData.parent_id = undefined
  formData.manager_id = undefined
  formData.is_active = true
  formRef.value?.clearValidate()
}

// Watch modelValue to populate form when editing
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      formData.name = newVal.name
      formData.code = newVal.code
      formData.description = newVal.description || ''
      formData.parent_id = newVal.parent_id || undefined
      formData.manager_id = newVal.manager_id || undefined
      formData.is_active = newVal.is_active
    } else {
      resetForm()
    }
  },
  { immediate: true }
)

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate((valid) => {
    if (valid) {
      // Build the payload (exclude is_active if creating, include if updating)
      const payload: DepartmentCreate | DepartmentUpdate = {
        name: formData.name,
        code: formData.code,
        description: formData.description || undefined,
        parent_id: formData.parent_id || undefined,
        manager_id: formData.manager_id || undefined,
      }

      // Include is_active only if updating (props.modelValue exists)
      if (props.modelValue) {
        (payload as DepartmentUpdate).is_active = formData.is_active
      }

      emit('submit', payload)
    }
  })
}

const validate = () => {
  return formRef.value?.validate()
}

// Expose methods for parent component
defineExpose({
  validate,
  resetForm,
  handleSubmit,
})

// Lifecycle
onMounted(async () => {
  // Load available departments for parent selection and employees for manager selection
  // Note: Using page_size=100 (API max). For large datasets, consider implementing
  // remote search functionality where options load as user types.
  try {
    const [deptResponse, empResponse] = await Promise.all([
      getDepartments({ page_size: 100 }),
      getEmployees({ page_size: 100 }),
    ])

    if (deptResponse.status === 200 && deptResponse.data) {
      availableParents.value = deptResponse.data.data
    }

    if (empResponse.status === 200 && empResponse.data) {
      availableEmployees.value = empResponse.data.data
    }
  } catch (error) {
    console.error('Error loading departments or employees:', error)
  }
})
</script>

<style scoped>
/* Add any custom form styles here */
</style>
