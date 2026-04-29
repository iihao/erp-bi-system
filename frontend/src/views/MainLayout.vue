<template>
  <div class="app-layout">
    <!-- 侧边栏导航 -->
    <nav-bar />

    <!-- 主内容区 -->
    <main class="main-content" :class="{ 'main-content-collapsed': isCollapsed }">
      <!-- 顶部导航栏 -->
      <header class="top-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/portal/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-for="(item, index) in breadcrumbs" :key="index">
              {{ item }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <!-- 刷新按钮 -->
          <el-button circle @click="refreshPage">
            <el-icon :class="{ 'is-loading': isRefreshing }"><Refresh /></el-icon>
          </el-button>

          <!-- 全屏切换 -->
          <el-button circle @click="toggleFullscreen">
            <el-icon><FullScreen /></el-icon>
          </el-button>

          <!-- 通知 -->
          <el-badge :value="3" :hidden="notificationCount === 0" class="notification-badge">
            <el-button circle>
              <el-icon><Bell /></el-icon>
            </el-button>
          </el-badge>

          <!-- 用户信息 -->
          <el-dropdown trigger="click">
            <div class="user-avatar">
              <el-avatar :size="32" :icon="User" />
              <span class="username">{{ username }}</span>
              <el-icon><CaretBottom /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item>
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided>
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 页面内容 -->
      <div class="page-wrapper">
        <transition name="fade" mode="out-in">
          <router-view />
        </transition>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, FullScreen, Bell, User, CaretBottom, Setting, SwitchButton } from '@element-plus/icons-vue'
import NavBar from '@/components/NavBar.vue'

const route = useRoute()

const isCollapsed = ref(false)
const isFullscreen = ref(false)
const isRefreshing = ref(false)
const notificationCount = ref(3)

const username = computed(() => localStorage.getItem('username') || '管理员')

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  return matched.map(item => item.meta.title)
})

// 刷新页面
const refreshPage = async () => {
  isRefreshing.value = true
  // 直接刷新当前页面，避免跳转到不存在的 /redirect 路由
  window.location.reload()
  isRefreshing.value = false
}

// 全屏切换
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
      isFullscreen.value = false
    }
  }
}

// 监听侧边栏折叠状态（从 NavBar 同步）
const updateCollapsedState = () => {
  const collapsed = localStorage.getItem('sidebarCollapsed')
  isCollapsed.value = collapsed === 'true'
}

onMounted(() => {
  updateCollapsedState()
  window.addEventListener('storage', updateCollapsedState)
})

onUnmounted(() => {
  window.removeEventListener('storage', updateCollapsedState)
})
</script>

<style scoped>
/* ========================================
   应用布局 - 专业左右结构
   ======================================== */
.app-layout {
  min-height: 100vh;
  background-color: var(--bg-body);
}

/* 主内容区 */
.main-content {
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  transition: margin-left var(--transition-slow) var(--transition-cubic);
}

.main-content-collapsed {
  margin-left: var(--sidebar-collapsed-width);
}

/* 顶部导航栏 */
.top-header {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: var(--header-height);
  padding: 0 var(--spacing-6);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-light);
  box-shadow: var(--shadow-xs);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

/* 面包屑 */
:deep(.el-breadcrumb) {
  font-size: var(--text-sm);
}

:deep(.el-breadcrumb__inner) {
  color: var(--text-tertiary);
}

:deep(.el-breadcrumb__inner a) {
  color: var(--text-secondary);
  transition: color var(--transition-fast) var(--transition-cubic);
}

:deep(.el-breadcrumb__inner a:hover) {
  color: var(--primary);
}

:deep(.el-breadcrumb__separator) {
  color: var(--slate-300);
}

/* 头部右侧 */
.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.header-right :deep(.el-button) {
  color: var(--text-secondary);
  border-color: transparent;
  background: transparent;
}

.header-right :deep(.el-button:hover) {
  background: var(--slate-100);
  color: var(--primary);
}

/* 通知徽章 */
.notification-badge {
  cursor: pointer;
}

.notification-badge :deep(.el-badge__content) {
  border: 2px solid var(--bg-surface);
}

/* 用户头像下拉 */
.user-avatar {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--transition-fast) var(--transition-cubic);
}

.user-avatar:hover {
  background: var(--slate-100);
}

.username {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.user-avatar :deep(.el-icon) {
  font-size: 14px;
  color: var(--text-tertiary);
}

/* 页面内容包装器 */
.page-wrapper {
  padding: var(--spacing-6);
  min-height: calc(100vh - var(--header-height));
}

/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-normal) var(--transition-cubic),
              transform var(--transition-normal) var(--transition-cubic);
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式 */
@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }

  .top-header {
    padding: 0 var(--spacing-4);
  }

  .username {
    display: none;
  }

  .page-wrapper {
    padding: var(--spacing-4);
  }
}
</style>
