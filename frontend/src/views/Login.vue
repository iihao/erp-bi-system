<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="login-background">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
      <div class="bg-grid"></div>
    </div>

    <div class="login-wrapper">
      <!-- 左侧品牌区 -->
      <div class="login-brand">
        <div class="brand-content">
          <div class="brand-logo">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="4" y="4" width="40" height="40" rx="8" fill="url(#logo-gradient)"/>
              <path d="M14 28V20L24 14L34 20V28L24 34L14 28Z" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M24 14V24" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M14 20L24 26L34 20" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
              <defs>
                <linearGradient id="logo-gradient" x1="4" y1="4" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                  <stop stop-color="#3B82F6"/>
                  <stop offset="1" stop-color="#1D4ED8"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 class="brand-title">AI数据融合平台</h1>
          <p class="brand-subtitle">企业级商业智能分析平台</p>
          
          <div class="brand-features">
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="22,4 12,14.01 9,11.01" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>智能数据分析</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M3 9h18" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M9 21V9" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>可视化报表</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 6v6l4 2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>实时监控</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="login-form-container">
        <div class="login-form-wrapper">
          <div class="form-header">
            <h2 class="form-title">欢迎登录</h2>
            <p class="form-subtitle">请输入您的账号信息</p>
          </div>

          <form @submit.prevent="handleLogin" class="login-form">
            <div class="form-group">
              <label for="username" class="form-label">
                <svg class="label-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="7" r="4" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                用户名
              </label>
              <div class="input-wrapper">
                <input
                  id="username"
                  v-model="username"
                  type="text"
                  placeholder="请输入用户名"
                  required
                  autocomplete="username"
                  class="form-input"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="password" class="form-label">
                <svg class="label-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="16" r="1" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M7 11V7a5 5 0 0110 0v4" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                密码
              </label>
              <div class="input-wrapper">
                <input
                  id="password"
                  v-model="password"
                  type="password"
                  placeholder="请输入密码"
                  required
                  autocomplete="current-password"
                  class="form-input"
                />
              </div>
            </div>

            <div class="form-options">
              <label class="checkbox-wrapper">
                <input type="checkbox" v-model="rememberMe" class="checkbox-input" />
                <span class="checkbox-text">记住我</span>
              </label>
              <a href="#" class="forgot-link">忘记密码？</a>
            </div>

            <button type="submit" class="login-button" :disabled="loading">
              <span v-if="!loading" class="button-content">
                <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4" stroke-linecap="round" stroke-linejoin="round"/>
                  <polyline points="10,17 15,12 10,7" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="15" y1="12" x2="3" y2="12" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                登 录
              </span>
              <span v-else class="button-loading">
                <svg class="loading-spinner" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-opacity="0.2"/>
                  <path d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                </svg>
                登录中...
              </span>
            </button>

            <div v-if="error" class="error-message">
              <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="16" x2="12.01" y2="16" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ error }}
            </div>
          </form>

          <div class="form-footer">
            <div class="divider">
              <span>或</span>
            </div>
            <button type="button" class="back-button" @click="goToAdmin">
              <svg class="back-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="19" y1="12" x2="5" y2="12" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="12,19 5,12 12,5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              返回后台管理
            </button>
          </div>
        </div>

        <div class="form-copyright">
          <p>© 2025 AI数据融合平台。All rights reserved.</p>
        </div>
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
/* ========================================
   登录页面 - 企业级专业风格
   ======================================== */

.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
  position: relative;
  overflow: hidden;
  padding: 20px;
}

/* 背景装饰 */
.login-background {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
  animation: float 20s ease-in-out infinite;
}

.shape-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  top: -200px;
  right: -200px;
}

.shape-2 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
  bottom: -150px;
  left: -150px;
  animation-delay: -5s;
}

.shape-3 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  opacity: 0.15;
  animation-delay: -10s;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse at center, black 20%, transparent 70%);
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.05);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.95);
  }
}

/* 主容器 */
.login-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  max-width: 1200px;
  width: 100%;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.4);
  position: relative;
  z-index: 1;
}

/* 左侧品牌区 */
.login-brand {
  background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
  padding: 60px 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-brand::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 30% 50%, rgba(59, 130, 246, 0.15) 0%, transparent 60%);
}

.brand-content {
  position: relative;
  z-index: 1;
}

.brand-logo {
  margin-bottom: 32px;
}

.brand-logo svg {
  width: 64px;
  height: 64px;
  filter: drop-shadow(0 8px 24px rgba(59, 130, 246, 0.4));
}

.brand-title {
  font-size: 32px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 12px 0;
  letter-spacing: 1px;
}

.brand-subtitle {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 40px 0;
  line-height: 1.6;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateX(4px);
}

.feature-icon {
  width: 20px;
  height: 20px;
  color: #60a5fa;
  flex-shrink: 0;
}

/* 右侧表单区 */
.login-form-container {
  padding: 60px 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: #ffffff;
}

.login-form-wrapper {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.form-header {
  margin-bottom: 40px;
}

.form-title {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.form-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

/* 表单样式 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.label-icon {
  width: 18px;
  height: 18px;
  color: #64748b;
}

.input-wrapper {
  position: relative;
}

.form-input {
  width: 100%;
  padding: 14px 16px;
  font-size: 15px;
  color: #0f172a;
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.form-input::placeholder {
  color: #94a3b8;
}

.form-input:hover {
  border-color: #cbd5e1;
  background: #ffffff;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

/* 表单选项 */
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.checkbox-input {
  width: 18px;
  height: 18px;
  accent-color: #3b82f6;
  cursor: pointer;
}

.checkbox-text {
  font-size: 14px;
  color: #64748b;
}

.forgot-link {
  font-size: 14px;
  color: #3b82f6;
  text-decoration: none;
  transition: color 0.2s ease;
}

.forgot-link:hover {
  color: #1d4ed8;
}

/* 登录按钮 */
.login-button {
  width: 100%;
  padding: 15px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3);
}

.login-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.button-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.button-icon {
  width: 20px;
  height: 20px;
}

.button-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 错误消息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 12px;
  color: #dc2626;
  font-size: 14px;
  animation: shake 0.5s ease;
}

.error-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-5px); }
  40%, 80% { transform: translateX(5px); }
}

/* 表单底部 */
.form-footer {
  margin-top: 32px;
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
  background: #e2e8f0;
}

.divider span {
  padding: 0 16px;
  color: #94a3b8;
  font-size: 13px;
}

.back-button {
  width: 100%;
  padding: 14px;
  background: #f1f5f9;
  color: #475569;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.back-button:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.back-icon {
  width: 18px;
  height: 18px;
}

/* 版权信息 */
.form-copyright {
  margin-top: 40px;
  text-align: center;
}

.form-copyright p {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 968px) {
  .login-wrapper {
    grid-template-columns: 1fr;
    max-width: 500px;
  }

  .login-brand {
    display: none;
  }

  .login-form-container {
    padding: 48px 40px;
  }
}

@media (max-width: 480px) {
  .login-container {
    padding: 16px;
  }

  .login-form-container {
    padding: 40px 32px;
  }

  .form-title {
    font-size: 24px;
  }

  .brand-title {
    font-size: 26px;
  }
}
</style>
