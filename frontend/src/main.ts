import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)

// Initialize auth store and wait for it to complete before mounting
// This prevents race condition between auth check and router guard
const authStore = useAuthStore()
authStore
  .initAuth()
  .catch(() => {
    // Silently handle init errors (user will be redirected to login by guard)
  })
  .finally(() => {
    // Mount app after auth initialization completes
    app.mount('#app')
  })
