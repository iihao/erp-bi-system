<template>
  <div class="portal-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ 'sidebar-collapse': isCollapse }">
      <div class="sidebar-header">
        <div class="logo">
          <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 3v18h18" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 17V9" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M13 17V5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 17v-3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span v-if="!isCollapse" class="logo-text">AI数据融合平台</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">
          <div class="nav-section-title" v-if="!isCollapse">
            <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/>
              <rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/>
            </svg>
            报表中心
          </div>
          <router-link to="/portal/dashboard" class="nav-item" exact-active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/>
              <rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/>
            </svg>
            <span v-if="!isCollapse">仪表板</span>
          </router-link>
          <router-link to="/portal/reports" class="nav-item" exact-active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
            <span v-if="!isCollapse">报表列表</span>
          </router-link>
        </div>

        <div class="nav-section">
          <div class="nav-section-title" v-if="!isCollapse">
            <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 21h18M5 21V7l8-4 8 4v14"/>
              <path d="M9 14h6"/>
            </svg>
            行业看板
          </div>
          <router-link to="/portal/realestate" class="nav-item" exact-active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 21h18M5 21V7l8-4 8 4v14"/>
              <path d="M9 14h6"/>
            </svg>
            <span v-if="!isCollapse">地产经营看板</span>
          </router-link>
        </div>

        <div class="nav-section">
          <div class="nav-section-title" v-if="!isCollapse">
            <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="12" y1="17" x2="12.01" y2="17" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            智能服务
          </div>
          <router-link to="/portal/ai-query" class="nav-item" exact-active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="12" y1="17" x2="12.01" y2="17" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span v-if="!isCollapse">AI 智能问数</span>
          </router-link>
          <router-link to="/portal/smart-report" class="nav-item" exact-active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 5h16"/>
              <path d="M4 12h16"/>
              <path d="M4 19h10"/>
            </svg>
            <span v-if="!isCollapse">AI 智能报表</span>
          </router-link>
          <router-link to="/portal/ai-chat" class="nav-item" exact-active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
              <line x1="9" y1="10" x2="15" y2="10"/>
              <line x1="12" y1="7" x2="12" y2="13"/>
            </svg>
            <span v-if="!isCollapse">AI 对话</span>
          </router-link>
        </div>

        <div class="nav-section" v-if="analysisReports.length > 0">
          <div class="nav-section-title" v-if="!isCollapse">
            <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            分析报表
          </div>
          <router-link
            v-for="report in analysisReports"
            :key="report.report_id"
            :to="`/portal/report/${report.report_id}`"
            class="nav-item"
            exact-active-class="active"
          >
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            <span v-if="!isCollapse">{{ report.report_name }}</span>
          </router-link>
        </div>

        <!-- 快捷入口 -->
        <div class="nav-section quick-access" v-if="!isCollapse">
          <div class="nav-section-title">快捷入口</div>
          <div class="quick-access-grid">
            <button class="quick-access-btn" title="刷新数据" @click="handleRefresh">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <button class="quick-access-btn" title="帮助中心" @click="handleHelp">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="17" x2="12.01" y2="17" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <button class="quick-access-btn" title="反馈建议" @click="handleFeedback">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
              </svg>
            </button>
          </div>
        </div>
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
      <!-- 顶部导航 -->
      <header class="portal-header">
        <div class="header-left">
          <button class="mobile-menu-btn" @click="toggleCollapse" v-if="isMobile">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
          
          <!-- 面包屑导航 -->
          <nav class="breadcrumb">
            <span class="breadcrumb-item">报表系统</span>
            <span v-if="currentReport" class="breadcrumb-separator">/</span>
            <span v-if="currentReport" class="breadcrumb-item active">{{ currentReport }}</span>
          </nav>
        </div>

        <div class="header-right">
          <!-- 通知 -->
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

          <el-dropdown class="user-menu" trigger="click" @command="handleUserCommand">
            <div class="user-info user-menu-trigger">
              <div class="avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <div class="user-meta">
                <span class="username">{{ username }}</span>
                <span class="role-badge" :class="roleClass">{{ roleName }}</span>
              </div>
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
                <el-dropdown-item v-if="canEnterAdmin" command="admin">
                  <svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 3v18h18"/>
                    <path d="M7 14v4"/>
                    <path d="M12 10v8"/>
                    <path d="M17 6v12"/>
                  </svg>
                  进入后台
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

      <!-- 内容区 -->
      <main class="portal-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()

const isCollapse = ref(false)
const isMobile = ref(false)
const username = ref('')
const userRole = ref(3)
const notificationCount = ref(2)

// 分析类报表（动态显示）
const analysisReports = ref([])

// 当前报表名称
const currentReport = computed(() => {
  const reportMap = {
    'sales-overview': '销售概览',
    'sales-trend': '销售趋势',
    'product-ranking': '产品排行',
    'category-analysis': '品类分析',
    'customer-analysis': '客户分析',
    'profit-analysis': '利润分析',
    'inventory-report': '库存报表',
    'forecast-report': '预测报表',
  }
  const reportId = route.params.id
  return reportMap[reportId] || null
})

// 角色名称和样式
const roleName = computed(() => {
  const names = { 1: '管理员', 2: '分析师', 3: '普通用户' }
  return names[userRole.value] || '普通用户'
})

const roleClass = computed(() => {
  const classes = { 1: 'role-admin', 2: 'role-analyst', 3: 'role-normal' }
  return classes[userRole.value] || 'role-normal'
})

const canEnterAdmin = computed(() => userRole.value === 1)

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

// 快捷操作
const handleRefresh = () => {
  ElMessage.success('数据已刷新')
  window.location.reload()
}

const handleHelp = () => {
  ElMessage.info('帮助中心功能开发中')
}

const handleFeedback = () => {
  ElMessage.info('反馈功能开发中')
}

// 通知中心
const handleNotifications = () => {
  ElMessage.info('通知中心功能开发中')
}

// 退出登录
const handleLogout = async () => {
  localStorage.removeItem('token')
  localStorage.removeItem('portal_username')
  ElMessage.success('已退出登录')
  router.push('/portal/login')
}

const handleUserCommand = (command) => {
  if (command === 'profile') {
    router.push('/profile')
    return
  }
  if (command === 'admin') {
    router.push('/admin/menu-hub')
    return
  }
  if (command === 'logout') {
    handleLogout()
  }
}

// 加载用户信息和可访问的报表
const loadUserInfo = async () => {
  username.value = localStorage.getItem('portal_username') || '用户'

  try {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/portal/login')
      return
    }

    // 获取报表列表（包含用户角色信息）
    const response = await fetch('/api/portal/overview', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      const data = await response.json()
      userRole.value = data.user_role || 3
      analysisReports.value = data.accessible_reports.filter(r =>
        ['customer-analysis', 'profit-analysis', 'inventory-report', 'forecast-report'].includes(r.report_id)
      )
    }
  } catch (error) {
    console.error('加载用户信息失败:', error)
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  loadUserInfo()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
/* ========================================
   前台布局 - 企业级专业风格
   ======================================== */

.portal-layout {
  display: flex;
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.14), transparent 28%),
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.12), transparent 24%),
    linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
}

/* ========================================
   侧边栏样式
   ======================================== */
.sidebar {
  width: var(--sidebar-width);
  background: linear-gradient(180deg, #0f2747 0%, #123c6b 55%, #164c86 100%);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-slow) var(--transition-cubic);
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: var(--z-fixed);
  height: 100vh;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.sidebar-collapse {
  width: var(--sidebar-collapsed-width);
}

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
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  overflow: hidden;
  white-space: nowrap;
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: #60a5fa;
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
  padding: 13px 12px;
  overflow-y: auto;
}

.nav-section {
  margin-bottom: 19px;
}

.nav-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-xs);
  color: rgba(219, 234, 254, 0.74);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 10px;
  padding-left: 10px;
  font-weight: var(--font-semibold);
}

.section-icon {
  width: 14px;
  height: 14px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: 10px 10px;
  color: rgba(226, 232, 240, 0.82);
  text-decoration: none;
  border-radius: var(--radius-lg);
  margin-bottom: 3px;
  transition: all var(--transition) var(--transition-cubic);
  cursor: pointer;
}

.nav-item:hover {
  background-color: rgba(59, 130, 246, 0.14);
  color: #ffffff;
  transform: translateX(2px);
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(191, 219, 254, 0.26) 0%, rgba(96, 165, 250, 0.16) 100%);
  color: #eff6ff;
  box-shadow: inset 0 0 0 1px rgba(191, 219, 254, 0.2);
}

.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* 快捷入口 */
.quick-access {
  margin-top: auto;
  padding-top: 13px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.quick-access-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.quick-access-btn {
  width: 100%;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-md);
  color: rgba(226, 232, 240, 0.7);
  cursor: pointer;
  transition: all var(--transition) var(--transition-cubic);
}

.quick-access-btn:hover {
  background: rgba(59, 130, 246, 0.18);
  color: #ffffff;
  border-color: rgba(191, 219, 254, 0.3);
}

.quick-access-btn svg {
  width: 16px;
  height: 16px;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 13px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.collapse-btn {
  width: 100%;
  height: 40px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg);
  color: rgba(226, 232, 240, 0.7);
  cursor: pointer;
  transition: all var(--transition) var(--transition-cubic);
  display: flex;
  align-items: center;
  justify-content: center;
}

.collapse-btn:hover {
  background: rgba(59, 130, 246, 0.18);
  color: #ffffff;
  border-color: rgba(191, 219, 254, 0.3);
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
  min-height: 100vh;
}

.main-with-collapse {
  margin-left: var(--sidebar-collapsed-width);
}

/* ========================================
   顶部导航栏
   ======================================== */
.portal-header {
  height: var(--header-height);
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
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

/* 面包屑导航 */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-sm);
}

.breadcrumb-item {
  color: #64748b;
}

.breadcrumb-item.active {
  color: #0f172a;
  font-weight: var(--font-medium);
}

.breadcrumb-separator {
  color: #cbd5e1;
}

/* 头部右侧 */
.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
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
  color: #64748b;
  cursor: pointer;
  border-radius: var(--radius);
  transition: all var(--transition) var(--transition-cubic);
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-btn:hover {
  background: rgba(59, 130, 246, 0.08);
  color: #2563eb;
}

.icon-btn svg {
  width: 20px;
  height: 20px;
}

/* 用户信息 */
.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-2) var(--spacing-4);
  background: rgba(248, 250, 252, 0.85);
  border-radius: var(--radius-2xl);
  transition: all var(--transition) var(--transition-cubic);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.user-menu {
  cursor: pointer;
}

.user-menu-trigger {
  min-width: 180px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #2563eb 0%, #0f766e 100%);
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
  color: #0f172a;
  font-weight: var(--font-medium);
}

.role-badge {
  font-size: var(--text-xs);
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-weight: var(--font-medium);
}

.dropdown-arrow {
  width: 14px;
  height: 14px;
  color: #64748b;
  flex-shrink: 0;
}

.dropdown-icon {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  vertical-align: -3px;
}

.dropdown-icon.danger {
  color: #dc2626;
}

.role-admin {
  background-color: #fee2e2;
  color: #b91c1c;
}

.role-analyst {
  background-color: #dbeafe;
  color: #1d4ed8;
}

.role-normal {
  background-color: #e2e8f0;
  color: #475569;
}

/* 退出登录按钮 */
.logout-btn {
  padding: var(--spacing-2);
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  border-radius: var(--radius);
  transition: all var(--transition) var(--transition-cubic);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logout-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

.logout-btn svg {
  width: 20px;
  height: 20px;
}

/* ========================================
   内容区
   ======================================== */
.portal-main {
  flex: 1;
  position: relative;
  padding: var(--spacing-6);
  overflow-y: auto;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.08), transparent 24%),
    linear-gradient(180deg, rgba(248, 251, 255, 0.8) 0%, rgba(238, 244, 251, 0.95) 100%);
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
   响应式设计
   ======================================== */
@media (max-width: 1024px) {
  .portal-main {
    padding: var(--spacing-4);
  }
}

@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
  }

  .sidebar:not(.sidebar-collapse) {
    transform: translateX(0);
  }

  .main-wrapper {
    margin-left: 0;
  }

  .main-with-collapse {
    margin-left: 0;
  }

  .mobile-menu-btn {
    display: flex;
  }

  .portal-header {
    padding: 0 var(--spacing-4);
  }

  .username {
    display: none;
  }

  .quick-access-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
