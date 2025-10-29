<template>
  <div class="employees-list">
    <div class="page-header">
      <h1>Employees</h1>
      <el-button type="primary">Add Employee</el-button>
    </div>

    <el-card>
      <div class="list-content">
        <p class="placeholder-text">Employee list will be implemented here.</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: 'EmployeesListPage',
})
</script>

<style scoped>
.employees-list {
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
