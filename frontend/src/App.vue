<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import router from '@/router'

// 验证 JWT token 是否有效
const isTokenValid = (token) => {
  if (!token) return false
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return false
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    if (payload.exp) {
      return payload.exp > Math.floor(Date.now() / 1000)
    }
    return true
  } catch {
    return false
  }
}

// 启动时强制校验 token，失效则跳转登录页
onMounted(() => {
  const token = localStorage.getItem('token')
  const currentPath = window.location.pathname
  const isLoginPage = currentPath === '/login' || currentPath === '/portal/login'

  if (token && !isTokenValid(token)) {
    console.warn('[App] Token 已过期，清除并跳转登录页')
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('portal_username')
    localStorage.removeItem('portal_token')
    if (!isLoginPage) {
      window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`
    }
  } else if (!token && !isLoginPage) {
    // 无 token 且不在登录页，也跳转登录页
    console.warn('[App] 无 token，跳转登录页')
    window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`
  }
})
</script>

<style>
/* ========================================
/* AI 智能报表系统全局样式 - 企业级专业风格 */
   基于设计令牌系统
   ======================================== */

/* 全局重置已在 design-tokens.css 中定义 */

#app {
  min-height: 100vh;
}

/* ========================================
   Element Plus 组件增强
   ======================================== */

/* 按钮 - 使用 Element Plus 默认样式，不覆盖 */

/* 卡片增强 */
.el-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition) var(--transition-cubic);
  overflow: hidden;
}

.el-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border);
}

.el-card__header {
  background: linear-gradient(135deg, var(--slate-50) 0%, #ffffff 100%);
  border-bottom: 1px solid var(--border-light);
  padding: 18px 24px;
}

.el-card__body {
  padding: 24px;
}

/* 输入框增强 */
.el-input__wrapper {
  border-radius: var(--radius-md);
  box-shadow: 0 0 0 1px var(--border-light) inset;
  transition: all var(--transition) var(--transition-cubic);
  padding: 10px 14px;
}

.el-input__wrapper:hover {
  box-shadow: 0 0 0 1px var(--border-dark) inset;
}

.el-input.is-focus .el-input__wrapper {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) inset;
  border-color: var(--primary);
}

/* 表格增强 */
.el-table {
  --el-table-header-bg-color: var(--slate-50);
  --el-table-row-hover-bg-color: var(--primary-50);
  --el-table-header-text-color: var(--text-secondary);
  font-size: var(--text-base);
}

.el-table th.el-table__cell {
  background-color: var(--slate-50);
  color: var(--text-secondary);
  font-weight: var(--font-semibold);
  border-bottom: 2px solid var(--border-light);
  padding: 14px 16px;
}

.el-table td.el-table__cell {
  padding: 14px 16px;
  border-color: var(--border-light);
  color: var(--text-secondary);
}

.el-table__body tr:hover > td {
  background-color: var(--primary-50);
}

/* 对话框增强 */
.el-dialog {
  border-radius: var(--radius-2xl);
  overflow: hidden;
  box-shadow: var(--shadow-2xl);
}

.el-dialog__header {
  background: linear-gradient(135deg, var(--slate-50) 0%, #ffffff 100%);
  padding: 24px 28px;
  border-bottom: 1px solid var(--border-light);
}

.el-dialog__title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.el-dialog__body {
  padding: 28px;
}

.el-dialog__footer {
  padding: 16px 28px;
  border-top: 1px solid var(--border-light);
  background: var(--slate-50);
}

/* 下拉菜单增强 */
.el-dropdown-menu {
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-light);
  padding: 8px;
}

.el-dropdown-menu__item {
  border-radius: var(--radius-md);
  padding: 10px 16px;
  transition: all var(--transition) var(--transition-cubic);
}

.el-dropdown-menu__item:hover {
  background-color: var(--slate-100);
}

/* 标签增强 */
.el-tag {
  border-radius: var(--radius-full);
  font-weight: var(--font-medium);
  padding: 4px 12px;
  border: none;
}

.el-tag--primary {
  background-color: var(--primary-100);
  color: var(--primary-700);
}

.el-tag--success {
  background-color: var(--success-100);
  color: var(--success-700);
}

.el-tag--warning {
  background-color: var(--warning-100);
  color: var(--warning-700);
}

.el-tag--danger {
  background-color: var(--danger-100);
  color: var(--danger-700);
}

/* 进度条增强 */
.el-progress__text {
  font-weight: var(--font-semibold);
}

/* 消息提示增强 */
.el-message {
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  border: none;
  padding: 14px 20px;
}

.el-message--success {
  background-color: var(--success-100);
  color: var(--success-700);
}

.el-message--warning {
  background-color: var(--warning-100);
  color: var(--warning-700);
}

.el-message--error {
  background-color: var(--danger-100);
  color: var(--danger-700);
}

.el-message--info {
  background-color: var(--info-100);
  color: var(--info-700);
}

/* 分页增强 */
.el-pagination {
  padding: 16px 0;
}

.el-pager li.is-active {
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%);
  color: #ffffff;
  border-radius: var(--radius-md);
}

.el-pager li:hover {
  color: var(--primary);
}

/* 菜单增强 */
.el-menu {
  border-right: none;
}

.el-menu-item {
  border-radius: var(--radius-md);
  margin: 4px 8px;
  transition: all var(--transition) var(--transition-cubic);
}

.el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.el-menu-item.is-active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.1) 100%);
  color: var(--primary-400);
}

/* 选择器增强 */
.el-select-dropdown__item.selected {
  color: var(--primary);
  font-weight: var(--font-semibold);
}

.el-select-dropdown__item:hover {
  background-color: var(--slate-100);
}

/* 加载增强 */
.el-loading-mask {
  border-radius: var(--radius-xl);
}

.el-loading-spinner .path {
  stroke: var(--primary);
}

.el-loading-spinner .el-loading-text {
  color: var(--text-secondary);
  margin-top: 12px;
  font-size: var(--text-sm);
}

/* 日期选择器增强 */
.el-picker-panel {
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--border-light);
}

.el-date-table td.today .el-date-table-cell__text {
  color: var(--primary);
  font-weight: var(--font-semibold);
}

.el-date-table td.current .el-date-table-cell__text {
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%);
}

/* 表单增强 */
.el-form-item__label {
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

/* 链接增强 */
.el-link.el-link--primary {
  color: var(--primary);
}

.el-link:hover {
  opacity: 0.8;
}

/* ========================================
   滚动条美化 (全局)
   ======================================== */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--slate-100);
  border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb {
  background: var(--slate-400);
  border-radius: var(--radius-full);
  transition: background var(--transition) var(--transition-cubic);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--slate-500);
}

/* ========================================
   文本选择样式
   ======================================== */
::selection {
  background-color: var(--primary-200);
  color: var(--primary-900);
}

/* ========================================
   聚焦可见性
   ======================================== */
:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
</style>
