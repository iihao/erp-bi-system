<template>
  <div class="admin-layout">
    <!-- 左侧菜单 -->
    <aside class="sidebar" :class="{ 'sidebar-collapse': isCollapse, 'sidebar-mobile': isMobile }">
      <div class="sidebar-header">
        <button type="button" class="logo" @click="goToMenuHub" title="返回功能导航">
          <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 3v18h18" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 17V9" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M13 17V5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 17v-3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span v-if="!isCollapse" class="logo-text">AI数据融合后台</span>
        </button>
      </div>

      <nav class="sidebar-nav">
        <el-menu
          :default-active="route.path"
          background-color="transparent"
          text-color="#94a3b8"
          active-text-color="#3b82f6"
          router
          :default-openeds="defaultOpenMenus"
          :collapse="isCollapse"
          :collapse-transition="false"
          :unique-opened="true"
        >
          <el-sub-menu index="dashboard">
            <template #title>
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 3v18h18"/>
                <path d="M7 14v4"/>
                <path d="M12 10v8"/>
                <path d="M17 6v12"/>
              </svg>
              <span>管理驾驶舱</span>
            </template>
            <el-menu-item index="/admin/dashboard">系统概况</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="system">
            <template #title>
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2a10 10 0 1010 10A10 10 0 0012 2zm0 18a8 8 0 118-8 8 8 0 01-8 8z"/>
                <path d="M12 6a6 6 0 106 6 6 6 0 00-6-6z"/>
                <circle cx="12" cy="12" r="2"/>
              </svg>
              <span>系统管理</span>
            </template>
            <el-menu-item index="/admin/users">用户管理</el-menu-item>
            <el-menu-item index="/admin/roles">角色管理</el-menu-item>
            <el-menu-item index="/admin/permissions">权限管理</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="data">
            <template #title>
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <ellipse cx="12" cy="5" rx="9" ry="3"/>
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
              </svg>
              <span>数据资源管理</span>
            </template>
            <el-menu-item index="/admin/datasources">数据源管理</el-menu-item>
            <el-menu-item index="/admin/standard-sql">标准 SQL 库</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="etl">
            <template #title>
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="9" y1="9" x2="21" y2="9"/>
                <line x1="9" y1="15" x2="21" y2="15"/>
                <line x1="9" y1="3" x2="9" y2="21"/>
              </svg>
              <span>ETL 开发</span>
            </template>
            <el-menu-item index="/admin/etl/tasks">任务管理</el-menu-item>
            <el-menu-item index="/admin/etl/jobs">作业定义</el-menu-item>
            <el-menu-item index="/admin/etl/schedules">调度配置</el-menu-item>
            <el-menu-item index="/admin/etl/development">数据开发</el-menu-item>
            <el-menu-item index="/admin/etl/editor">ETL 编辑器</el-menu-item>
            <el-menu-item index="/admin/etl/logs">执行日志</el-menu-item>
            <el-menu-item index="/admin/etl/monitor">监控告警</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="report">
            <template #title>
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="20" x2="18" y2="10"/>
                <line x1="12" y1="20" x2="12" y2="4"/>
                <line x1="6" y1="20" x2="6" y2="14"/>
              </svg>
              <span>报表管理</span>
            </template>
            <el-menu-item index="/admin/reports">报表列表</el-menu-item>
            <el-menu-item index="/admin/reports/designer">报表设计器</el-menu-item>
            <el-menu-item index="/admin/reports/designer-pro">高级报表设计器</el-menu-item>
            <el-menu-item index="/admin/bi/dashboard">可视化报表</el-menu-item>
            <el-menu-item index="/admin/bi/reports">我的报表</el-menu-item>
            <el-menu-item index="/admin/bi/metabase">Metabase BI</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="ai">
            <template #title>
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="17" x2="12.01" y2="17" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>AI 智能分析</span>
            </template>
            <el-menu-item index="/admin/ai-query">AI 配置中心</el-menu-item>
            <el-menu-item index="/admin/ai-query-simple">AI 问数（优化版）</el-menu-item>
            <el-menu-item index="/admin/ai-enhanced">智能问数</el-menu-item>
            <el-menu-item index="/admin/ai-report">AI 智能报表</el-menu-item>
            <el-menu-item index="/portal/ai-chat">AI 对话（Chat）</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="monitor">
            <template #title>
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
              <span>监控管理</span>
            </template>
            <el-menu-item index="/admin/monitor/system">系统信息</el-menu-item>
            <el-menu-item index="/admin/monitor/logs">系统日志</el-menu-item>
            <el-menu-item index="/admin/monitor/ai-records">问数记录</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="system2">
            <template #title>
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
              <span>系统设置</span>
            </template>
            <el-menu-item index="/admin/system/ai-config"> AI 配置</el-menu-item>
            <el-menu-item index="/admin/system/update-logs"> 更新日志</el-menu-item>
          </el-sub-menu>

          <div class="menu-divider"></div>

          <el-menu-item index="/dashboard">
            <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            <span>返回前台</span>
          </el-menu-item>
        </el-menu>
      </nav>

      <div class="sidebar-footer">
        <button class="collapse-btn" @click="toggleCollapse" :title="isCollapse ? '展开菜单' : '收起菜单'">
          <svg class="collapse-icon" :class="{ 'collapsed': isCollapse }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-wrapper" :class="{ 'main-with-collapse': isCollapse }">
      <header class="header">
        <div class="header-left">
          <button class="mobile-menu-btn" @click="toggleMobileMenu" v-if="isMobile">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
          
          <!-- 页面标题 -->
          <button type="button" class="page-title" @click="goToMenuHub" title="返回功能导航">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            <span>{{ currentPageTitle }}</span>
          </button>
        </div>

        <div class="header-right">
          <!-- 全局搜索 -->
          <div class="global-search">
            <el-input
              v-model="searchQuery"
              placeholder="搜索功能、菜单..."
              class="search-input"
              size="default"
              clearable
              @keyup.enter="handleGlobalSearch"
            >
              <template #prefix>
                <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="M21 21l-4.35-4.35" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </template>
            </el-input>
          </div>

          <!-- 通知中心 -->
          <div class="notification-center">
            <el-badge :value="notificationCount" :hidden="notificationCount === 0" class="notification-badge">
              <button class="icon-btn" @click="handleNotifications" title="通知中心">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                  <path d="M13.73 21a2 2 0 01-3.46 0"/>
                </svg>
              </button>
            </el-badge>
          </div>

          <!-- 用户下拉菜单 -->
          <el-dropdown class="user-dropdown" trigger="click" @command="handleUserCommand">
            <div class="user-info">
              <div class="avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <span class="username">{{ username }}</span>
              <svg class="dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
                  </svg>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <svg class="dropdown-icon danger" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
                    <polyline points="16 17 21 12 16 7"/>
                    <line x1="21" y1="12" x2="9" y2="12"/>
                  </svg>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- 移动端遮罩层 -->
    <div class="mobile-overlay" v-if="isMobile && !isCollapse" @click="toggleMobileMenu"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()

const isCollapse = ref(false)  // 默认展开
const isMobile = ref(false)
const username = computed(() => localStorage.getItem('username') || '管理员')
const searchQuery = ref('')
const notificationCount = ref(3)

// 默认展开的菜单（动态跟随当前路由所在分组）
const defaultOpenMenus = computed(() => {
  const menuMap = {
    '/admin/dashboard': 'dashboard',
    '/admin/users': 'system',
    '/admin/roles': 'system',
    '/admin/permissions': 'system',
    '/admin/datasources': 'data',
    '/admin/standard-sql': 'data',
    '/admin/etl/tasks': 'etl',
    '/admin/etl/jobs': 'etl',
    '/admin/etl/schedules': 'etl',
    '/admin/etl/development': 'etl',
    '/admin/etl/editor': 'etl',
    '/admin/etl/logs': 'etl',
    '/admin/etl/monitor': 'etl',
    '/admin/reports': 'report',
    '/admin/reports/designer': 'report',
    '/admin/reports/designer-pro': 'report',
    '/admin/bi/dashboard': 'report',
    '/admin/bi/reports': 'report',
    '/admin/bi/metabase': 'report',
    '/admin/ai-query': 'ai',
    '/admin/ai-query-simple': 'ai',
    '/admin/ai-enhanced': 'ai',
    '/admin/ai-report': 'ai',
    '/portal/ai-chat': 'ai',
    '/admin/monitor/system': 'monitor',
    '/admin/monitor/logs': 'monitor',
    '/admin/monitor/ai-records': 'monitor',
    '/admin/system/ai-config': 'system2',
    '/admin/system/update-logs': 'system2',
  }
  const activeMenu = menuMap[route.path]
  return activeMenu ? [activeMenu] : []
})

// 页面标题映射
const pageTitles = {
  '/admin/dashboard': '系统概况',
  '/admin/users': '用户管理',
  '/admin/roles': '角色管理',
  '/admin/permissions': '权限管理',
  '/admin/datasources': '数据源管理',
  '/admin/standard-sql': '标准 SQL 库',
  '/admin/etl/tasks': '任务管理',
  '/admin/etl/jobs': '作业定义',
  '/admin/etl/schedules': '调度配置',
  '/admin/etl/development': '数据开发',
  '/admin/etl/editor': 'ETL 编辑器',
  '/admin/etl/logs': '执行日志',
  '/admin/etl/monitor': '监控告警',
  '/admin/reports': '报表列表',
  '/admin/reports/designer': '报表设计器',
  '/admin/reports/designer-pro': '高级报表设计器',
  '/admin/bi/dashboard': '可视化报表',
  '/admin/bi/reports': '我的报表',
  '/admin/bi/metabase': 'Metabase BI',
  '/admin/ai-query': 'AI 配置中心',
  '/admin/ai-query-simple': 'AI 问数（优化版）',
  '/admin/ai-enhanced': '智能问数',
  '/admin/ai-report': 'AI 智能报表',
  '/portal/ai-chat': 'AI 对话',
  '/admin/monitor/system': '系统信息',
  '/admin/monitor/logs': '系统日志',
  '/admin/monitor/ai-records': '问数记录',
  '/admin/system/ai-config': 'AI 配置',
  '/admin/system/update-logs': '更新日志',
}

// 当前页面标题
const currentPageTitle = computed(() => {
  // 优先使用路由 meta 标题，未配置时再兜底映射
  const metaTitle = route.meta?.title
  if (metaTitle) return metaTitle
  const path = route.path
  return pageTitles[path] || '管理后台'
})

// 检测移动端
const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value) {
    isCollapse.value = true
  }
}

// 切换侧边栏
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 切换移动端菜单
const toggleMobileMenu = () => {
  isCollapse.value = !isCollapse.value
}

// 返回后台功能导航首页
const goToMenuHub = () => {
  if (route.path !== '/admin/menu-hub') {
    router.push('/admin/menu-hub')
  }
}

// 全局搜索
const handleGlobalSearch = () => {
  if (searchQuery.value.trim()) {
    ElMessage.info(`搜索：${searchQuery.value}`)
  }
}

// 通知中心
const handleNotifications = () => {
  ElMessage.info('通知中心功能开发中')
}

// 用户菜单命令
const handleUserCommand = async (command) => {
  switch (command) {
    case 'profile':
      ElMessage.info('个人中心功能开发中')
      break
    case 'settings':
      ElMessage.info('系统设置功能开发中')
      break
    case 'logout':
      await handleLogout()
      break
  }
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 取消退出
  }
}

// 验证 token 是否有效
const isTokenValid = (token) => {
  if (!token) return false
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return false
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    if (payload.exp) {
      const now = Math.floor(Date.now() / 1000)
      return payload.exp >= now
    }
    return true
  } catch {
    return false
  }
}

// 页面加载时验证 token
onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  
  const token = localStorage.getItem('token')
  if (!token || !isTokenValid(token)) {
    ElMessage.error('登录已过期，请重新登录')
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/login')
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
/* 导入 Admin 通用样式规范 */
@import './styles/common.css';

/* ========================================
   管理后台布局 - 企业级专业风格
   ======================================== */

.admin-layout {
  display: flex;
  height: 100vh;
  background-color: var(--bg-body);
  position: relative;
}

/* ========================================
   侧边栏样式
   ======================================== */
.sidebar {
  width: var(--sidebar-width);
  background: linear-gradient(180deg, var(--bg-sidebar) 0%, var(--bg-sidebar-dark) 100%);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-slow) var(--transition-cubic);
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: var(--z-fixed);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.sidebar-collapse {
  width: var(--sidebar-collapsed-width);
}

.sidebar-mobile {
  transform: translateX(-100%);
}

.sidebar-mobile:not(.sidebar-collapse) {
  transform: translateX(0);
}

/* 侧边栏头部 */
.sidebar-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 var(--spacing-4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.logo {
  appearance: none;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  overflow: hidden;
  white-space: nowrap;
  cursor: pointer;
  padding: 0;
  color: inherit;
  text-align: left;
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: var(--primary-400);
  flex-shrink: 0;
}

.logo-text {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: #ffffff;
  letter-spacing: -0.5px;
}

/* 侧边栏导航 */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-4) 0;
}

.sidebar-nav :deep(.el-menu) {
  border-right: none;
  background: transparent !important;
}

/* 一级菜单 */
.sidebar-nav :deep(.el-sub-menu__title),
.sidebar-nav > :deep(.el-menu-item) {
  color: #94a3b8 !important;
  font-size: var(--text-sm) !important;
  font-weight: var(--font-medium) !important;
  height: 44px !important;
  line-height: 44px !important;
  border-radius: var(--radius);
  margin: 2px 8px;
  padding-left: 24px !important;
  transition: all var(--transition) var(--transition-cubic);
}

/* 二级菜单项 - 固定缩进 24px */
.sidebar-nav :deep(.el-menu--inline) {
  background: transparent !important;
}

.sidebar-nav :deep(.el-menu--inline .el-menu-item) {
  padding-left: 48px !important;
  height: 35px !important;
  line-height: 35px !important;
  font-size: var(--text-sm) !important;
  background: transparent !important;
  margin: 2px 8px !important;
  border-radius: var(--radius) !important;
}

/* 二级菜单选中状态 - 保持缩进 */
.sidebar-nav :deep(.el-menu--inline .el-menu-item.is-active) {
  padding-left: 48px !important;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.1) 100%) !important;
  color: var(--primary-400) !important;
  border-left: 3px solid var(--primary-400) !important;
}

.sidebar-nav :deep(.el-sub-menu__title:hover),
.sidebar-nav :deep(.el-menu-item:hover) {
  background: rgba(59, 130, 246, 0.1) !important;
  color: #ffffff !important;
}

.sidebar-nav :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.1) 100%) !important;
  color: var(--primary-400) !important;
  border-left: 3px solid var(--primary-400);
  padding-left: 21px !important;
}

.sidebar-nav :deep(.el-sub-menu__title *) {
  color: #94a3b8 !important;
}

.sidebar-nav :deep(.el-sub-menu__title:hover *) {
  color: #ffffff !important;
}

/* 确保下拉触发文字始终可见 */
.sidebar-nav :deep(.el-sub-menu__title .el-select__selected-item),
.sidebar-nav :deep(.el-sub-menu__title .el-input__inner) {
  color: #ffffff !important;
}

/* 菜单图标 */
.menu-icon {
  width: 18px;
  height: 18px;
  margin-right: 12px;
  flex-shrink: 0;
}

.menu-emoji {
  margin-right: 12px;
  font-size: 18px;
}

.menu-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: var(--spacing-4) var(--spacing-3);
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: var(--spacing-4);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.collapse-btn {
  width: 100%;
  height: 40px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg);
  color: #94a3b8;
  cursor: pointer;
  transition: all var(--transition) var(--transition-cubic);
  display: flex;
  align-items: center;
  justify-content: center;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.2);
}

.collapse-icon {
  width: 18px;
  height: 18px;
  transition: transform var(--transition) var(--transition-cubic);
}

.collapse-icon.collapsed {
  transform: rotate(180deg);
}

/* ========================================
   主内容区
   ======================================== */
.main-wrapper {
  flex: 1;
  margin-left: var(--sidebar-width);
  transition: margin-left var(--transition-slow) var(--transition-cubic);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-with-collapse {
  margin-left: var(--sidebar-collapsed-width);
}

/* ========================================
   顶部导航栏
   ======================================== */
.header {
  height: var(--header-height);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-6);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  box-shadow: var(--shadow-xs);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  flex: 1;
  min-width: 0;
}

.mobile-menu-btn {
  display: none;
  padding: var(--spacing-2);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius);
  transition: all var(--transition) var(--transition-cubic);
}

.mobile-menu-btn:hover {
  background: var(--bg-surface-secondary);
  color: var(--text-primary);
}

.mobile-menu-btn svg {
  width: 24px;
  height: 24px;
}

/* 页面标题 - 替代面包屑 */
.page-title {
  appearance: none;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  white-space: nowrap;
  cursor: pointer;
  padding: 0;
  text-align: left;
}

.page-title svg {
  width: 22px;
  height: 22px;
  color: var(--primary);
  flex-shrink: 0;
}

/* 头部右侧 */
.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

/* 全局搜索 */
.global-search {
  width: 280px;
}

.search-input {
  width: 100%;
}

.search-input :deep(.el-input__wrapper) {
  background: var(--bg-surface-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 0 var(--spacing-3);
  transition: all var(--transition) var(--transition-cubic);
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: var(--primary-light);
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-icon {
  width: 18px;
  height: 18px;
  color: var(--text-tertiary);
}

/* 通知中心 */
.notification-center {
  display: flex;
  align-items: center;
}

.notification-badge {
  cursor: pointer;
}

.icon-btn {
  padding: var(--spacing-2);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius);
  transition: all var(--transition) var(--transition-cubic);
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-btn:hover {
  background: var(--bg-surface-secondary);
  color: var(--primary);
}

.icon-btn svg {
  width: 20px;
  height: 20px;
}

/* 用户下拉菜单 */
.user-dropdown {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--bg-surface-secondary);
  border-radius: var(--radius-2xl);
  transition: all var(--transition) var(--transition-cubic);
}

.user-info:hover {
  background: var(--slate-200);
}

.avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-700) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar svg {
  width: 18px;
  height: 18px;
  color: #ffffff;
}

.username {
  font-size: var(--text-sm);
  color: var(--text-primary);
  font-weight: var(--font-medium);
}

.dropdown-arrow {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
}

.dropdown-icon {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  vertical-align: middle;
}

.dropdown-icon.danger {
  color: var(--danger);
}

/* ========================================
   内容区域
   ======================================== */
.content {
  flex: 1;
  overflow-y: auto;
  background: var(--bg-body);
  padding: 0;
}

/* 页面容器 - 统一内边距 */
.content > * {
  padding: var(--spacing-6);
}

/* ========================================
   Admin 表格统一样式
   ======================================== */
.content :deep(.el-table) {
  width: 100% !important;
  --el-table-border-color: var(--border-light);
  --el-table-header-bg-color: #f1f5f9;
  --el-table-row-hover-bg-color: #f1f5f9;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.content :deep(.el-table th.el-table__cell) {
  background: #f1f5f9 !important;
  color: var(--text-secondary);
  font-weight: var(--font-semibold);
  padding-top: 10px;
  padding-bottom: 10px;
}

.content :deep(.el-table td.el-table__cell) {
  padding-top: 10px;
  padding-bottom: 10px;
}

.content :deep(.el-table .cell) {
  line-height: 1.45;
}

.content :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.content :deep(.pagination-container),
.content :deep(.pagination) {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--border-light);
}

/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition) var(--transition-cubic);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ========================================
   移动端遮罩层
   ======================================== */
.mobile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: calc(var(--z-fixed) - 1);
  animation: fadeIn var(--transition) var(--transition-cubic);
}

/* ========================================
   响应式设计
   ======================================== */
@media (max-width: 1024px) {
  .global-search {
    width: 200px;
  }
}

@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
  }

  .global-search {
    display: none;
  }

  .username {
    display: none;
  }

  .header {
    padding: 0 var(--spacing-4);
  }

  .content > * {
    padding: var(--spacing-4);
  }

  .sidebar {
    box-shadow: var(--shadow-2xl);
  }

  .content :deep(.el-table) {
    font-size: 13px;
  }
}
</style>
