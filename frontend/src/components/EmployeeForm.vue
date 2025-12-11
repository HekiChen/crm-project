<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-width="140px"
    @submit.prevent="handleSubmit"
  >
    <!-- Basic Information -->
    <div class="form-section">
      <h3>Basic Information</h3>
      <el-form-item label="Employee Number" prop="employee_number">
        <el-input 
          v-model="formData.employee_number" 
          placeholder="e.g., EMP-001"
          :disabled="isEditing" 
        />
      </el-form-item>
      <el-form-item label="First Name" prop="first_name">
        <el-input v-model="formData.first_name" placeholder="Enter first name" />
      </el-form-item>
      <el-form-item label="Last Name" prop="last_name">
        <el-input v-model="formData.last_name" placeholder="Enter last name" />
      </el-form-item>
      <el-form-item label="Email" prop="email">
        <el-input v-model="formData.email" type="email" placeholder="employee@example.com" />
      </el-form-item>
    </div>

    <!-- Work Information -->
    <div class="form-section">
      <h3>Work Information</h3>
      <el-form-item label="Hire Date" prop="hire_date">
        <el-date-picker
          v-model="formData.hire_date"
          type="date"
          placeholder="Select hire date"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="Position" prop="position_id">
        <el-select 
          v-model="formData.position_id" 
          placeholder="Select position" 
          clearable
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="position in positions"
            :key="position.id"
            :label="position.name"
            :value="position.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="Department" prop="department_id">
        <el-select 
          v-model="formData.department_id" 
          placeholder="Select department" 
          clearable
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="department in departments"
            :key="department.id"
            :label="department.name"
            :value="department.id"
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
        >
          <el-option
            v-for="emp in managerOptions"
            :key="emp.id"
            :label="`${emp.first_name} ${emp.last_name} (${emp.employee_number})`"
            :value="emp.id"
          />
        </el-select>
      </el-form-item>
    </div>

    <!-- Contact Information -->
    <div class="form-section">
      <h3>Contact Information</h3>
      <el-form-item label="Phone" prop="phone">
        <el-input v-model="formData.phone" placeholder="+1-555-0123" />
      </el-form-item>
      <el-form-item label="Address Line 1" prop="address1">
        <el-input v-model="formData.address1" placeholder="Street address" />
      </el-form-item>
      <el-form-item label="Address Line 2" prop="address2">
        <el-input v-model="formData.address2" placeholder="Apt, suite, unit, etc. (optional)" />
      </el-form-item>
      <el-form-item label="City" prop="city">
        <el-input v-model="formData.city" placeholder="City" />
      </el-form-item>
      <el-form-item label="State" prop="state">
        <el-input v-model="formData.state" placeholder="State/Province" />
      </el-form-item>
      <el-form-item label="ZIP Code" prop="zip_code">
        <el-input v-model="formData.zip_code" placeholder="12345" />
      </el-form-item>
      <el-form-item label="Country" prop="country">
        <el-input v-model="formData.country" placeholder="US" />
      </el-form-item>
    </div>

    <!-- Status -->
    <div class="form-section">
      <h3>Status</h3>
      <el-form-item label="Active" prop="is_active">
        <el-switch
          v-model="formData.is_active"
          active-text="Active"
          inactive-text="Inactive"
        />
      </el-form-item>
    </div>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { Employee, EmployeeCreate, EmployeeUpdate } from '@/types/employee'
import type { Position } from '@/types/position'
import type { Department } from '@/types/department'

interface Props {
  modelValue?: Employee | null
  positions: Position[]
  departments: Department[]
  activeEmployees: Employee[]
}

interface Emits {
  (e: 'submit', data: EmployeeCreate | EmployeeUpdate): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  positions: () => [],
  departments: () => [],
  activeEmployees: () => [],
})

const emit = defineEmits<Emits>()

// Form ref
const formRef = ref<FormInstance>()

// Form data
const formData = reactive<EmployeeCreate & { is_active: boolean }>({
  employee_number: '',
  first_name: '',
  last_name: '',
  email: '',
  hire_date: '',
  position_id: null,
  department_id: null,
  manager_id: null,
  phone: null,
  address1: null,
  address2: null,
  city: null,
  state: null,
  zip_code: null,
  country: 'US',
  is_active: true,
})

// Computed: Check if form is in edit mode
const isEditing = computed(() => !!props.modelValue)

// Computed manager options (exclude current employee if editing)
const managerOptions = computed(() => {
  if (!props.modelValue) {
    return props.activeEmployees
  }
  
  // Exclude the current employee from manager options
  return props.activeEmployees.filter(emp => emp.id !== props.modelValue!.id)
})

// Validation rules
const rules: FormRules = {
  employee_number: [
    { required: true, message: 'Employee number is required', trigger: 'blur' },
    { min: 2, max: 50, message: 'Employee number must be between 2 and 50 characters', trigger: 'blur' },
  ],
  first_name: [
    { required: true, message: 'First name is required', trigger: 'blur' },
    { min: 1, max: 100, message: 'First name must be between 1 and 100 characters', trigger: 'blur' },
  ],
  last_name: [
    { required: true, message: 'Last name is required', trigger: 'blur' },
    { min: 1, max: 100, message: 'Last name must be between 1 and 100 characters', trigger: 'blur' },
  ],
  email: [
    { required: true, message: 'Email is required', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email address', trigger: 'blur' },
    { max: 255, message: 'Email cannot exceed 255 characters', trigger: 'blur' },
  ],
  hire_date: [
    { required: true, message: 'Hire date is required', trigger: 'change' },
  ],
  phone: [
    { max: 20, message: 'Phone number cannot exceed 20 characters', trigger: 'blur' },
  ],
  address1: [
    { max: 255, message: 'Address line 1 cannot exceed 255 characters', trigger: 'blur' },
  ],
  address2: [
    { max: 255, message: 'Address line 2 cannot exceed 255 characters', trigger: 'blur' },
  ],
  city: [
    { max: 100, message: 'City cannot exceed 100 characters', trigger: 'blur' },
  ],
  state: [
    { max: 100, message: 'State cannot exceed 100 characters', trigger: 'blur' },
  ],
  zip_code: [
    { max: 20, message: 'ZIP code cannot exceed 20 characters', trigger: 'blur' },
  ],
  country: [
    { max: 100, message: 'Country cannot exceed 100 characters', trigger: 'blur' },
  ],
}

// Methods
const resetForm = () => {
  formData.employee_number = ''
  formData.first_name = ''
  formData.last_name = ''
  formData.email = ''
  formData.hire_date = ''
  formData.position_id = null
  formData.department_id = null
  formData.manager_id = null
  formData.phone = null
  formData.address1 = null
  formData.address2 = null
  formData.city = null
  formData.state = null
  formData.zip_code = null
  formData.country = 'US'
  formData.is_active = true
  formRef.value?.clearValidate()
}

// Watch modelValue to populate form when editing
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      formData.employee_number = newVal.employee_number
      formData.first_name = newVal.first_name
      formData.last_name = newVal.last_name
      formData.email = newVal.email
      formData.hire_date = newVal.hire_date
      formData.position_id = newVal.position_id
      formData.department_id = newVal.department_id
      formData.manager_id = newVal.manager_id || null
      formData.phone = newVal.phone || null
      formData.address1 = newVal.address1 || null
      formData.address2 = newVal.address2 || null
      formData.city = newVal.city || null
      formData.state = newVal.state || null
      formData.zip_code = newVal.zip_code || null
      formData.country = newVal.country || 'US'
      formData.is_active = newVal.is_active ?? true
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
      // Build the payload
      const payload: EmployeeCreate | EmployeeUpdate = {
        employee_number: formData.employee_number,
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        hire_date: formData.hire_date,
        position_id: formData.position_id,
        department_id: formData.department_id,
        manager_id: formData.manager_id || null,
        phone: formData.phone || null,
        address1: formData.address1 || null,
        address2: formData.address2 || null,
        city: formData.city || null,
        state: formData.state || null,
        zip_code: formData.zip_code || null,
        country: formData.country || null,
      }

      // Include is_active only if updating (props.modelValue exists)
      if (props.modelValue) {
        (payload as EmployeeUpdate).is_active = formData.is_active
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
</script>

<style scoped>
.form-section {
  margin-bottom: 24px;
}

.form-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
  color: #303133;
}

.form-section:last-child {
  margin-bottom: 0;
}
</style>
