<template>
  <div class="not-found">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <h2 class="error-message">Page Not Found</h2>
      <p class="error-description">
        The page you are looking for might have been removed, had its name changed, or is
        temporarily unavailable.
      </p>
      <el-button type="primary" @click="goHome">Go to Dashboard</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

defineOptions({
  name: 'NotFoundPage',
})

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f0f2f5;
  padding: 20px;
}

.not-found-content {
  text-align: center;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  color: #409eff;
  margin: 0;
  line-height: 1;
}

.error-message {
  font-size: 32px;
  font-weight: 600;
  color: #303133;
  margin: 20px 0 16px 0;
}

.error-description {
  font-size: 16px;
  color: #606266;
  margin: 0 0 32px 0;
  max-width: 500px;
}

@media (max-width: 768px) {
  .error-code {
    font-size: 80px;
  }

  .error-message {
    font-size: 24px;
  }

  .error-description {
    font-size: 14px;
  }
}
</style>
