<template>
  <el-dialog
    v-model="dialogVisible"
    title="Work Log Details"
    width="700px"
    @close="handleClose"
  >
    <div v-if="workLog" class="work-log-details">
      <!-- Employee & Log Info -->
      <div class="info-section">
        <div class="info-row">
          <span class="label">Employee:</span>
          <span class="value">
            {{ workLog.employee?.first_name }} {{ workLog.employee?.last_name }}
            ({{ workLog.employee?.email }})
          </span>
        </div>
        <div class="info-row">
          <span class="label">Log Type:</span>
          <el-tag :type="getLogTypeTagType(workLog.log_type)">
            {{ formatLogType(workLog.log_type) }}
          </el-tag>
        </div>
        <div class="info-row">
          <span class="label">Period:</span>
          <span class="value">{{ formatPeriod(workLog.start_date, workLog.end_date) }}</span>
        </div>
        <div class="info-row">
          <span class="label">Created:</span>
          <span class="value">{{ formatDateTime(workLog.created_at) }}</span>
        </div>
        <div v-if="workLog.updated_at !== workLog.created_at" class="info-row">
          <span class="label">Updated:</span>
          <span class="value">{{ formatDateTime(workLog.updated_at) }}</span>
        </div>
      </div>

      <el-divider />

      <!-- Progress -->
      <div class="content-section">
        <h4 class="section-title">Progress</h4>
        <div class="content-text">{{ workLog.progress }}</div>
      </div>

      <!-- Issues -->
      <div v-if="workLog.issues" class="content-section">
        <h4 class="section-title">Issues</h4>
        <div class="content-text">{{ workLog.issues }}</div>
      </div>

      <!-- Plans -->
      <div v-if="workLog.plans" class="content-section">
        <h4 class="section-title">Plans</h4>
        <div class="content-text">{{ workLog.plans }}</div>
      </div>

      <el-divider />

      <!-- Rating Section -->
      <div class="rating-section">
        <h4 class="section-title">Rating</h4>
        <div v-if="workLog.rating" class="rating-display">
          <div class="stars">
            <el-rate
              :model-value="workLog.rating"
              disabled
              show-score
              text-color="#ff9900"
            />
          </div>
          <div class="rating-info">
            <div class="rated-by">
              Rated by: {{ workLog.rater?.first_name }} {{ workLog.rater?.last_name }}
            </div>
            <div class="rated-at">{{ formatDateTime(workLog.rated_at!) }}</div>
          </div>
        </div>
        <div v-else class="no-rating">
          <el-text type="info">Not rated yet</el-text>
        </div>

        <!-- Rate Button (for managers) -->
        <div v-if="canRate" class="rate-action">
          <el-button type="primary" @click="handleRateClick">
            {{ workLog.rating ? 'Update Rating' : 'Rate Work Log' }}
          </el-button>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">Close</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { WorkLog, LogType } from '@/types/workLog'

interface Props {
  visible: boolean
  workLog: WorkLog | null
  canRate?: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'rate', workLog: WorkLog): void
}

const props = withDefaults(defineProps<Props>(), {
  canRate: false,
})
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)

// Watch visibility prop
watch(
  () => props.visible,
  (val) => {
    dialogVisible.value = val
  }
)

// Watch dialogVisible to emit update
watch(dialogVisible, (val) => {
  emit('update:visible', val)
})

function formatLogType(logType: LogType): string {
  const types = {
    daily: 'Daily',
    weekly: 'Weekly',
    monthly: 'Monthly',
    yearly: 'Yearly',
  }
  return types[logType] || logType
}

function getLogTypeTagType(logType: LogType): string {
  const types = {
    daily: '',
    weekly: 'success',
    monthly: 'warning',
    yearly: 'danger',
  }
  return types[logType] || ''
}

function formatPeriod(startDate: string, endDate: string): string {
  const start = new Date(startDate).toLocaleDateString()
  const end = new Date(endDate).toLocaleDateString()
  return startDate === endDate ? start : `${start} - ${end}`
}

function formatDateTime(dateTime: string): string {
  return new Date(dateTime).toLocaleString()
}

function handleRateClick() {
  if (props.workLog) {
    emit('rate', props.workLog)
  }
}

function handleClose() {
  dialogVisible.value = false
}
</script>

<style scoped>
.work-log-details {
  padding: 0 8px;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.label {
  font-weight: 600;
  color: #606266;
  min-width: 80px;
}

.value {
  color: #303133;
}

.content-section {
  margin: 16px 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
}

.content-text {
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.rating-section {
  margin-top: 16px;
}

.rating-display {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stars {
  display: flex;
  align-items: center;
}

.rating-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 14px;
  color: #909399;
}

.rated-by {
  font-weight: 500;
  color: #606266;
}

.rated-at {
  font-size: 12px;
}

.no-rating {
  padding: 12px 0;
}

.rate-action {
  margin-top: 16px;
}

:deep(.el-divider) {
  margin: 20px 0;
}

:deep(.el-rate) {
  height: auto;
}

:deep(.el-rate__text) {
  font-size: 16px;
  font-weight: 600;
}
</style>
