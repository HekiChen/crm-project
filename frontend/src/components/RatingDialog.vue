<template>
  <el-dialog
    v-model="dialogVisible"
    title="Rate Work Log"
    width="400px"
    @close="handleClose"
  >
    <div class="rating-dialog-content">
      <div v-if="workLog" class="work-log-summary">
        <div class="summary-row">
          <span class="label">Employee:</span>
          <span class="value">
            {{ workLog.employee?.first_name }} {{ workLog.employee?.last_name }}
          </span>
        </div>
        <div class="summary-row">
          <span class="label">Period:</span>
          <span class="value">{{ formatPeriod(workLog.start_date, workLog.end_date) }}</span>
        </div>
      </div>

      <el-divider />

      <div class="rating-input">
        <div class="rating-label">Select Rating</div>
        <el-rate
          v-model="rating"
          :max="5"
          show-text
          :texts="['Poor', 'Fair', 'Good', 'Very Good', 'Excellent']"
          size="large"
        />
      </div>

      <div v-if="rating > 0" class="confirmation-text">
        Rate this work log <strong>{{ rating }}/5 stars</strong>?
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">Cancel</el-button>
      <el-button
        type="primary"
        :disabled="rating === 0"
        :loading="loading"
        @click="handleSubmit"
      >
        Submit Rating
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { rateWorkLog } from '@/api/workLogs'
import type { WorkLog } from '@/types/workLog'

interface Props {
  visible: boolean
  workLog: WorkLog | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const rating = ref(0)
const loading = ref(false)

// Watch visibility prop
watch(
  () => props.visible,
  (val) => {
    dialogVisible.value = val
    if (val && props.workLog) {
      // If editing existing rating, pre-populate
      rating.value = props.workLog.rating || 0
    } else {
      rating.value = 0
    }
  }
)

// Watch dialogVisible to emit update
watch(dialogVisible, (val) => {
  emit('update:visible', val)
})

function formatPeriod(startDate: string, endDate: string): string {
  const start = new Date(startDate).toLocaleDateString()
  const end = new Date(endDate).toLocaleDateString()
  return startDate === endDate ? start : `${start} - ${end}`
}

async function handleSubmit() {
  if (!props.workLog || rating.value === 0) return

  loading.value = true
  try {
    await rateWorkLog(props.workLog.id, { rating: rating.value })
    ElMessage.success('Work log rated successfully')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('Failed to rate work log:', error)
    ElMessage.error('Failed to rate work log')
  } finally {
    loading.value = false
  }
}

function handleClose() {
  rating.value = 0
  dialogVisible.value = false
}
</script>

<style scoped>
.rating-dialog-content {
  padding: 0 8px;
}

.work-log-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.label {
  font-weight: 600;
  color: #606266;
  min-width: 70px;
}

.value {
  color: #303133;
}

.rating-input {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 20px 0;
}

.rating-label {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.confirmation-text {
  text-align: center;
  padding: 12px;
  background-color: #f0f9ff;
  border-radius: 4px;
  color: #409eff;
  margin-top: 16px;
}

:deep(.el-divider) {
  margin: 16px 0;
}

:deep(.el-rate) {
  height: auto;
}

:deep(.el-rate__text) {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  margin-left: 12px;
}
</style>
