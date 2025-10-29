<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1 class="login-title">CRM System</h1>
        <p class="login-subtitle">Sign in to your account</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleSubmit"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="Email"
            size="large"
            clearable
            :prefix-icon="User"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="Password"
            size="large"
            show-password
            :prefix-icon="Lock"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleSubmit"
          >
            {{ loading ? 'Signing in...' : 'Sign In' }}
          </el-button>
        </el-form-item>

        <el-alert
          v-if="errorMessage"
          :title="errorMessage"
          type="error"
          :closable="false"
          show-icon
          class="login-error"
        />
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

// Set component name to satisfy multi-word requirement
defineOptions({
  name: 'LoginPage',
})

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Form ref
const loginFormRef = ref<FormInstance>()

// Form state
const loginForm = reactive({
  username: '',
  password: '',
})

// Form validation rules
const loginRules: FormRules = {
  username: [
    { required: true, message: 'Please enter your email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email', trigger: ['blur', 'change'] },
  ],
  password: [
    { required: true, message: 'Please enter your password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' },
  ],
}

// Component state
const loading = ref(false)
const errorMessage = ref('')

// Handle form submission
const handleSubmit = async () => {
  if (!loginFormRef.value) return

  try {
    // Validate form
    await loginFormRef.value.validate()

    // Clear previous error
    errorMessage.value = ''
    loading.value = true

    // Attempt login
    await authStore.login(loginForm.username, loginForm.password)

    // Show success message
    ElMessage.success('Login successful!')

    // Redirect to intended page or dashboard
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.push(redirect)
  } catch (error: unknown) {
    // Show error message
    const err = error as { response?: { data?: { error?: { message?: string } } }; message?: string }
    errorMessage.value =
      err.response?.data?.error?.message ||
      err.message ||
      'Login failed. Please check your credentials and try again.'

    console.error('Login error:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.login-form {
  margin-top: 24px;
}

.login-button {
  width: 100%;
  margin-top: 8px;
}

.login-error {
  margin-top: 16px;
}

/* Responsive design */
@media (max-width: 768px) {
  .login-box {
    padding: 30px 20px;
  }

  .login-title {
    font-size: 24px;
  }
}
</style>
