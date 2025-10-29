<template>
  <div class="work-logs-list">
    <div class="page-header">
      <h1>Recent Activities (Work Logs)</h1>
      <el-button type="primary">Add Work Log</el-button>
    </div>

    <el-card>
      <div class="list-content">
        <p class="placeholder-text">Work log list (last 7 days) will be implemented here.</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: 'WorkLogsListPage',
})
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

.list-content {
  padding: 40px;
  text-align: center;
}

.placeholder-text {
  color: #909399;
  font-size: 14px;
}
</style>
