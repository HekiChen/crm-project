<template>
  <div class="work-logs-list">
    <div class="page-header">
      <h1>Work Logs</h1>
      <div class="header-actions">
        <el-button @click="handleExport" :loading="exportLoading">
          <el-icon><Download /></el-icon>
          Export to CSV
        </el-button>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          Add Work Log
        </el-button>
      </div>
    </div>

    <!-- Tabs -->
    <el-card shadow="never">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="My Work Logs" name="my">
          <!-- Filters -->
          <div class="filter-bar">
            <el-form :inline="true">
              <el-form-item label="Log Type">
                <el-select
                  v-model="filters.log_type"
                  placeholder="All Types"
                  clearable
                  style="width: 140px"
                  @change="loadWorkLogs"
                >
                  <el-option label="Daily" value="daily" />
                  <el-option label="Weekly" value="weekly" />
                  <el-option label="Monthly" value="monthly" />
                  <el-option label="Yearly" value="yearly" />
                </el-select>
              </el-form-item>
              <el-form-item label="Date Range">
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="To"
                  start-placeholder="Start date"
                  end-placeholder="End date"
                  style="width: 280px"
                  @change="handleDateRangeChange"
                />
              </el-form-item>
              <el-form-item>
                <el-button @click="clearFilters">Clear Filters</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- My Work Logs Table -->
          <el-table
            v-loading="loading"
            :data="workLogs"
            style="width: 100%"
            stripe
          >
            <el-table-column label="Log Type" width="100">
              <template #default="{ row }">
                <el-tag :type="getLogTypeTagType(row.log_type)" size="small">
                  {{ formatLogType(row.log_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Period" width="200">
              <template #default="{ row }">
                {{ formatPeriod(row.start_date, row.end_date) }}
              </template>
            </el-table-column>
            <el-table-column label="Progress" min-width="300">
              <template #default="{ row }">
                <div class="progress-text">{{ truncateText(row.progress, 100) }}</div>
              </template>
            </el-table-column>
            <el-table-column label="Rating" width="120">
              <template #default="{ row }">
                <div v-if="row.rating" class="rating-display">
                  <el-rate :model-value="row.rating" disabled size="small" />
                </div>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column label="Created" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="Actions" width="200" fixed="right">
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
              <el-empty description="No work logs found" />
            </template>
          </el-table>

          <!-- Pagination -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.page_size"
              :total="pagination.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </el-tab-pane>

        <!-- Team Work Logs Tab (Managers Only) -->
        <el-tab-pane v-if="isManager" label="Team Work Logs" name="team">
          <!-- Team Filters -->
          <div class="filter-bar">
            <el-form :inline="true">
              <el-form-item label="Log Type">
                <el-select
                  v-model="teamFilters.log_type"
                  placeholder="All Types"
                  clearable
                  style="width: 140px"
                  @change="loadTeamWorkLogs"
                >
                  <el-option label="Daily" value="daily" />
                  <el-option label="Weekly" value="weekly" />
                  <el-option label="Monthly" value="monthly" />
                  <el-option label="Yearly" value="yearly" />
                </el-select>
              </el-form-item>
              <el-form-item label="Date Range">
                <el-date-picker
                  v-model="teamDateRange"
                  type="daterange"
                  range-separator="To"
                  start-placeholder="Start date"
                  end-placeholder="End date"
                  style="width: 280px"
                  @change="handleTeamDateRangeChange"
                />
              </el-form-item>
              <el-form-item label="Rating">
                <el-checkbox
                  v-model="teamFilters.has_rating"
                  @change="loadTeamWorkLogs"
                >
                  Has Rating
                </el-checkbox>
              </el-form-item>
              <el-form-item>
                <el-button @click="clearTeamFilters">Clear Filters</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- Team Work Logs Table -->
          <el-table
            v-loading="teamLoading"
            :data="teamWorkLogs"
            style="width: 100%"
            stripe
          >
            <el-table-column label="Employee" width="180">
              <template #default="{ row }">
                {{ row.employee?.first_name }} {{ row.employee?.last_name }}
              </template>
            </el-table-column>
            <el-table-column label="Log Type" width="100">
              <template #default="{ row }">
                <el-tag :type="getLogTypeTagType(row.log_type)" size="small">
                  {{ formatLogType(row.log_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Period" width="200">
              <template #default="{ row }">
                {{ formatPeriod(row.start_date, row.end_date) }}
              </template>
            </el-table-column>
            <el-table-column label="Progress" min-width="250">
              <template #default="{ row }">
                <div class="progress-text">{{ truncateText(row.progress, 80) }}</div>
              </template>
            </el-table-column>
            <el-table-column label="Rating" width="120">
              <template #default="{ row }">
                <div v-if="row.rating" class="rating-display">
                  <el-rate :model-value="row.rating" disabled size="small" />
                </div>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column label="Created" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="Actions" width="150" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="handleView(row)">
                  <el-icon><View /></el-icon>
                </el-button>
                <el-button size="small" type="warning" @click="handleRate(row)">
                  <el-icon><Star /></el-icon>
                  Rate
                </el-button>
              </template>
            </el-table-column>

            <template #empty>
              <el-empty description="No team work logs found" />
            </template>
          </el-table>

          <!-- Team Pagination -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="teamPagination.page"
              v-model:page-size="teamPagination.page_size"
              :total="teamPagination.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleTeamSizeChange"
              @current-change="handleTeamPageChange"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- Dialogs -->
    <WorkLogForm
      v-model:visible="formVisible"
      :work-log="selectedWorkLog"
      @success="handleFormSuccess"
    />

    <WorkLogDetails
      v-model:visible="detailsVisible"
      :work-log="selectedWorkLog"
      :can-rate="activeTab === 'team' && isManager"
      @rate="handleRate"
    />

    <RatingDialog
      v-model:visible="ratingVisible"
      :work-log="selectedWorkLog"
      @success="handleRatingSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Edit, Delete, Star, Download } from '@element-plus/icons-vue'
import { getWorkLogs, getTeamWorkLogs, deleteWorkLog } from '@/api/workLogs'
import { useAuthStore } from '@/stores/auth'
import type { WorkLog, LogType, WorkLogFilter } from '@/types/workLog'
import WorkLogForm from '@/components/WorkLogForm.vue'
import WorkLogDetails from '@/components/WorkLogDetails.vue'
import RatingDialog from '@/components/RatingDialog.vue'

const authStore = useAuthStore()

const activeTab = ref('my')
const loading = ref(false)
const teamLoading = ref(false)
const exportLoading = ref(false)
const formVisible = ref(false)
const detailsVisible = ref(false)
const ratingVisible = ref(false)
const selectedWorkLog = ref<WorkLog | null>(null)

const workLogs = ref<WorkLog[]>([])
const teamWorkLogs = ref<WorkLog[]>([])
const dateRange = ref<[Date, Date] | null>(null)
const teamDateRange = ref<[Date, Date] | null>(null)

const filters = reactive<WorkLogFilter>({
  log_type: undefined,
  start_date: undefined,
  end_date: undefined,
  page: 1,
  page_size: 20,
})

const teamFilters = reactive<WorkLogFilter>({
  log_type: undefined,
  start_date: undefined,
  end_date: undefined,
  has_rating: undefined,
  page: 1,
  page_size: 20,
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const teamPagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// Check if current user is a manager
const isManager = computed(() => {
  // TODO: Implement proper manager check based on auth store
  // For now, assume user is manager if they have direct reports
  return true // Placeholder
})

onMounted(() => {
  loadWorkLogs()
})

async function loadWorkLogs() {
  loading.value = true
  try {
    const params = {
      ...filters,
      page: pagination.page,
      page_size: pagination.page_size,
    }
    const response = await getWorkLogs(params)
    workLogs.value = response.data.data
    pagination.total = response.data.total
  } catch (error) {
    console.error('Failed to load work logs:', error)
    ElMessage.error('Failed to load work logs')
  } finally {
    loading.value = false
  }
}

async function loadTeamWorkLogs() {
  teamLoading.value = true
  try {
    const params = {
      ...teamFilters,
      page: teamPagination.page,
      page_size: teamPagination.page_size,
    }
    const response = await getTeamWorkLogs(params)
    teamWorkLogs.value = response.data.data
    teamPagination.total = response.data.total
  } catch (error) {
    console.error('Failed to load team work logs:', error)
    ElMessage.error('Failed to load team work logs')
  } finally {
    teamLoading.value = false
  }
}

function handleTabChange(tab: string) {
  if (tab === 'team' && teamWorkLogs.value.length === 0) {
    loadTeamWorkLogs()
  }
}

function handleDateRangeChange(value: [Date, Date] | null) {
  if (value) {
    filters.start_date = value[0].toISOString().split('T')[0]
    filters.end_date = value[1].toISOString().split('T')[0]
  } else {
    filters.start_date = undefined
    filters.end_date = undefined
  }
  loadWorkLogs()
}

function handleTeamDateRangeChange(value: [Date, Date] | null) {
  if (value) {
    teamFilters.start_date = value[0].toISOString().split('T')[0]
    teamFilters.end_date = value[1].toISOString().split('T')[0]
  } else {
    teamFilters.start_date = undefined
    teamFilters.end_date = undefined
  }
  loadTeamWorkLogs()
}

function clearFilters() {
  filters.log_type = undefined
  filters.start_date = undefined
  filters.end_date = undefined
  dateRange.value = null
  loadWorkLogs()
}

function clearTeamFilters() {
  teamFilters.log_type = undefined
  teamFilters.start_date = undefined
  teamFilters.end_date = undefined
  teamFilters.has_rating = undefined
  teamDateRange.value = null
  loadTeamWorkLogs()
}

function handlePageChange(page: number) {
  pagination.page = page
  loadWorkLogs()
}

function handleSizeChange(size: number) {
  pagination.page_size = size
  pagination.page = 1
  loadWorkLogs()
}

function handleTeamPageChange(page: number) {
  teamPagination.page = page
  loadTeamWorkLogs()
}

function handleTeamSizeChange(size: number) {
  teamPagination.page_size = size
  teamPagination.page = 1
  loadTeamWorkLogs()
}

function handleCreate() {
  selectedWorkLog.value = null
  formVisible.value = true
}

function handleEdit(workLog: WorkLog) {
  selectedWorkLog.value = workLog
  formVisible.value = true
}

function handleView(workLog: WorkLog) {
  selectedWorkLog.value = workLog
  detailsVisible.value = true
}

function handleRate(workLog: WorkLog) {
  selectedWorkLog.value = workLog
  ratingVisible.value = true
}

async function handleDelete(workLog: WorkLog) {
  try {
    await ElMessageBox.confirm(
      'Are you sure you want to delete this work log?',
      'Warning',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
      }
    )

    await deleteWorkLog(workLog.id)
    ElMessage.success('Work log deleted successfully')
    loadWorkLogs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete work log:', error)
      ElMessage.error('Failed to delete work log')
    }
  }
}

function handleFormSuccess() {
  loadWorkLogs()
  if (activeTab.value === 'team') {
    loadTeamWorkLogs()
  }
}

function handleRatingSuccess() {
  loadTeamWorkLogs()
}

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

function formatDate(dateTime: string): string {
  return new Date(dateTime).toLocaleDateString()
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

function handleExport() {
  exportLoading.value = true
  try {
    // Get the current data to export
    const dataToExport = activeTab.value === 'my' ? workLogs.value : teamWorkLogs.value
    
    if (dataToExport.length === 0) {
      ElMessage.warning('No work logs to export')
      return
    }

    // Prepare CSV content
    const headers = ['Log Type', 'Start Date', 'End Date', 'Employee', 'Progress', 'Issues', 'Plans', 'Rating', 'Rated By', 'Created At']
    const csvRows = []
    
    // Add header row
    csvRows.push(headers.join(','))
    
    // Add data rows
    dataToExport.forEach((log) => {
      const row = [
        log.log_type,
        log.start_date,
        log.end_date,
        `"${log.employee?.first_name || ''} ${log.employee?.last_name || ''}"`,
        `"${(log.progress || '').replace(/"/g, '""')}"`,
        `"${(log.issues || '').replace(/"/g, '""')}"`,
        `"${(log.plans || '').replace(/"/g, '""')}"`,
        log.rating || '',
        log.rated_by ? `"${log.rated_by.first_name || ''} ${log.rated_by.last_name || ''}"` : '',
        new Date(log.created_at).toLocaleString(),
      ]
      csvRows.push(row.join(','))
    })
    
    // Create CSV blob
    const csvContent = csvRows.join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    
    // Create download link
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    const filename = `work_logs_${activeTab.value}_${new Date().toISOString().split('T')[0]}.csv`
    link.setAttribute('download', filename)
    link.style.visibility = 'hidden'
    
    // Trigger download
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('Work logs exported successfully')
  } catch (error) {
    console.error('Failed to export work logs:', error)
    ElMessage.error('Failed to export work logs')
  } finally {
    exportLoading.value = false
  }
}
</script>

<style scoped>
.work-logs-list {
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

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-bar {
  margin-bottom: 16px;
}

.progress-text {
  line-height: 1.4;
  color: #606266;
}

.text-muted {
  color: #909399;
}

.rating-display {
  display: flex;
  align-items: center;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

:deep(.el-tabs__content) {
  padding: 16px 0 0 0;
}

:deep(.el-rate) {
  height: auto;
}
</style>
