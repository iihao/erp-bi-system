<template>
  <div class="portal-login-container">
    <div class="login-box">
      <div class="logo-section">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 3v18h18" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 17V9" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M13 17V5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 17v-3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1 class="title">AI数据融合平台</h1>
        <p class="subtitle">专业数据分析与商业智能平台</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-item">
          <label for="username">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            用户名
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="请输入用户名"
            required
            autocomplete="username"
          />
        </div>

        <div class="form-item">
          <label for="password">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <circle cx="12" cy="16" r="1"/>
              <path d="M7 11V7a5 5 0 0110 0v4"/>
            </svg>
            密码
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码"
            required
            autocomplete="current-password"
          />
        </div>

        <div class="form-options">
          <label class="checkbox-label">
            <input type="checkbox" v-model="rememberMe" />
            <span>记住我</span>
          </label>
        </div>

        <button type="submit" class="login-btn" :disabled="loading">
          <span v-if="!loading">登 录</span>
          <span v-else>登录中...</span>
        </button>

        <p v-if="error" class="error-message">{{ error }}</p>

        <div class="divider">
          <span>或</span>
        </div>

        <button type="button" class="back-btn" @click="goToAdmin">
          返回后台管理
        </button>
      </form>

      <div class="footer-info">
        <p>© 2025 AI数据融合平台。All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const loading = ref(false)
const error = ref('')

// 检查是否已登录
onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) {
    // 验证 token 是否有效
    try {
      const parts = token.split('.')
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
        if (!payload.exp || payload.exp > Math.floor(Date.now() / 1000)) {
          // Token 有效，跳转到门户
          router.push('/portal')
          return
        }
      }
    } catch (e) {}
    // Token 无效或过期，清除
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('portal_username')
  }
  // 从 localStorage 读取记住的用户名
  const savedUsername = localStorage.getItem('portal_username')
  if (savedUsername) {
    username.value = savedUsername
    rememberMe.value = true
  }
})

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  try {
    const res = await api.login({
      username: username.value,
      password: password.value
    })
    localStorage.setItem('token', res.token)
    localStorage.setItem('portal_username', username.value)

    if (rememberMe.value) {
      localStorage.setItem('portal_remember', 'true')
    } else {
      localStorage.removeItem('portal_remember')
    }

    ElMessage.success('登录成功')

    // 检查是否有 redirect 参数
    const redirect = route.query.redirect
    if (redirect) {
      router.push(redirect)
    } else {
      router.push('/portal')
    }
  } catch (err) {
    error.value = err.detail || err.message || '登录失败，请检查用户名和密码'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

const goToAdmin = () => {
  router.push('/login')
}
</script>

<style scoped>
.portal-login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.portal-login-container::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
  animation: pulse 20s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1) rotate(0deg); }
  50% { transform: scale(1.1) rotate(180deg); }
}

.login-box {
  background: rgba(255, 255, 255, 0.98);
  padding: 48px 44px;
  border-radius: 16px;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.4);
  width: 100%;
  max-width: 440px;
  position: relative;
  z-index: 1;
}

.logo-section {
  text-align: center;
  margin-bottom: 36px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.3);
}

.logo-icon svg {
  width: 36px;
  height: 36px;
  color: white;
}

.title {
  font-size: 26px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
  letter-spacing: 1px;
}

.subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.login-form {
  margin-top: 24px;
}

.form-item {
  margin-bottom: 22px;
}

.form-item label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: #475569;
  font-weight: 500;
  font-size: 14px;
}

.input-icon {
  width: 16px;
  height: 16px;
  color: #64748b;
}

.form-item input {
  width: 100%;
  padding: 14px 16px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.3s;
  background-color: #f8fafc;
  color: #1e293b;
  box-sizing: border-box;
}

.form-item input::placeholder {
  color: #94a3b8;
}

.form-item input:focus {
  outline: none;
  border-color: #2563eb;
  background-color: #fff;
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.form-options {
  margin-bottom: 24px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #64748b;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #2563eb;
  cursor: pointer;
}

.login-btn {
  width: 100%;
  padding: 15px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  letter-spacing: 2px;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(37, 99, 235, 0.4);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  color: #dc2626;
  font-size: 14px;
  margin-top: 16px;
  padding: 12px 14px;
  background-color: rgba(220, 38, 38, 0.1);
  border-radius: 8px;
  text-align: center;
}

.divider {
  display: flex;
  align-items: center;
  margin: 24px 0;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background-color: #e2e8f0;
}

.divider span {
  padding: 0 16px;
  color: #94a3b8;
  font-size: 13px;
}

.back-btn {
  width: 100%;
  padding: 14px;
  background-color: #f1f5f9;
  color: #475569;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  background-color: #e2e8f0;
  color: #1e293b;
}

.footer-info {
  margin-top: 32px;
  text-align: center;
}

.footer-info p {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
}

/* 响应式 */
@media (max-width: 480px) {
  .login-box {
    padding: 36px 28px;
    margin: 20px;
  }

  .title {
    font-size: 22px;
  }

  .logo-icon {
    width: 56px;
    height: 56px;
  }

  .logo-icon svg {
    width: 30px;
    height: 30px;
  }
}
</style>
