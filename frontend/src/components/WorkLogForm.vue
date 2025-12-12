<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? 'Edit Work Log' : 'Create Work Log'"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
      label-position="left"
    >
      <el-form-item label="Log Type" prop="log_type">
        <el-radio-group v-model="formData.log_type" :disabled="isEdit">
          <el-radio label="daily">Daily</el-radio>
          <el-radio label="weekly">Weekly</el-radio>
          <el-radio label="monthly">Monthly</el-radio>
          <el-radio label="yearly">Yearly</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="Start Date" prop="start_date">
        <el-date-picker
          v-model="formData.start_date"
          type="date"
          placeholder="Select start date"
          :disabled="isEdit"
          style="width: 100%"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="Progress" prop="progress">
        <el-input
          v-model="formData.progress"
          type="textarea"
          :rows="4"
          placeholder="What did you accomplish?"
          maxlength="5000"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="Issues" prop="issues">
        <el-input
          v-model="formData.issues"
          type="textarea"
          :rows="3"
          placeholder="Any questions, blockers, or challenges? (optional)"
          maxlength="5000"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="Plans" prop="plans">
        <el-input
          v-model="formData.plans"
          type="textarea"
          :rows="3"
          placeholder="What are you planning next? (optional)"
          maxlength="5000"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">Cancel</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        {{ isEdit ? 'Update' : 'Create' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createWorkLog, updateWorkLog } from '@/api/workLogs'
import type { WorkLog, WorkLogCreate, WorkLogUpdate, LogType } from '@/types/workLog'

interface Props {
  visible: boolean
  workLog?: WorkLog | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const loading = ref(false)
const isEdit = ref(false)

const formData = reactive<WorkLogCreate>({
  log_type: 'daily' as LogType,
  start_date: '',
  progress: '',
  issues: null,
  plans: null,
})

const formRules: FormRules = {
  log_type: [{ required: true, message: 'Please select log type', trigger: 'change' }],
  start_date: [{ required: true, message: 'Please select start date', trigger: 'change' }],
  progress: [
    { required: true, message: 'Please enter progress', trigger: 'blur' },
    { min: 10, message: 'Progress must be at least 10 characters', trigger: 'blur' },
  ],
}

// Watch visibility prop
watch(
  () => props.visible,
  (val) => {
    dialogVisible.value = val
    if (val) {
      initForm()
    }
  }
)

// Watch dialogVisible to emit update
watch(dialogVisible, (val) => {
  emit('update:visible', val)
})

function initForm() {
  isEdit.value = !!props.workLog
  if (props.workLog) {
    // Edit mode - populate form
    formData.log_type = props.workLog.log_type
    formData.start_date = props.workLog.start_date
    formData.progress = props.workLog.progress
    formData.issues = props.workLog.issues || null
    formData.plans = props.workLog.plans || null
  } else {
    // Create mode - reset form
    resetForm()
  }
}

function resetForm() {
  formData.log_type = 'daily' as LogType
  formData.start_date = ''
  formData.progress = ''
  formData.issues = null
  formData.plans = null
  formRef.value?.clearValidate()
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      if (isEdit.value && props.workLog) {
        // Update existing work log
        const updateData: WorkLogUpdate = {
          progress: formData.progress,
          issues: formData.issues,
          plans: formData.plans,
        }
        await updateWorkLog(props.workLog.id, updateData)
        ElMessage.success('Work log updated successfully')
      } else {
        // Create new work log
        await createWorkLog(formData)
        ElMessage.success('Work log created successfully')
      }
      emit('success')
      handleClose()
    } catch (error) {
      console.error('Failed to save work log:', error)
      ElMessage.error('Failed to save work log')
    } finally {
      loading.value = false
    }
  })
}

function handleClose() {
  resetForm()
  dialogVisible.value = false
}
</script>

<style scoped>
:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-textarea__inner) {
  font-family: inherit;
}
</style>
