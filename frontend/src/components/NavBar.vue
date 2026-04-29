<template>
  <aside class="sidebar" :class="{ 'sidebar-collapsed': isCollapsed }">
    <!-- Logo 区域 -->
    <div class="sidebar-header">
      <div class="logo-wrapper">
        <div class="logo-icon">
          <el-icon :size="24"><DataLine /></el-icon>
        </div>
        <span class="logo-text" v-show="!isCollapsed">AI数据融合平台</span>
      </div>
      <el-button class="collapse-btn" @click="toggleCollapse" link>
        <el-icon><Fold v-if="!isCollapsed" /><Expand v-else /></el-icon>
      </el-button>
    </div>

    <!-- 导航菜单 -->
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapsed"
      :collapse-transition="true"
      router
      class="sidebar-menu"
    >
      <!-- 前台导航 -->
      <div class="menu-section" v-show="!isCollapsed">
        <div class="menu-section-title">前台业务</div>
      </div>

      <el-menu-item index="/portal/dashboard">
        <el-icon><House /></el-icon>
        <template #title>门户首页</template>
      </el-menu-item>

      <el-menu-item index="/portal/reports">
        <el-icon><DataBoard /></el-icon>
        <template #title>报表中心</template>
      </el-menu-item>

      <el-menu-item index="/portal/ai-query">
        <el-icon><ChatDotRound /></el-icon>
        <template #title>AI 问数</template>
      </el-menu-item>

      <el-menu-item index="/data">
        <el-icon><DataLine /></el-icon>
        <template #title>数据预览</template>
      </el-menu-item>

      <el-menu-item index="/etl">
        <el-icon><Refresh /></el-icon>
        <template #title>ETL 任务</template>
      </el-menu-item>

      <!-- 后台管理分隔线 -->
      <el-divider v-show="!isCollapsed" />

      <!-- 后台管理 -->
      <div class="menu-section" v-show="!isCollapsed">
        <div class="menu-section-title">后台管理</div>
      </div>

      <el-menu-item index="/admin/dashboard">
        <el-icon><Monitor /></el-icon>
        <template #title>系统监控</template>
      </el-menu-item>

      <el-menu-item index="/admin/users">
        <el-icon><User /></el-icon>
        <template #title>用户管理</template>
      </el-menu-item>

      <el-menu-item index="/admin/roles">
        <el-icon><UserFilled /></el-icon>
        <template #title>角色管理</template>
      </el-menu-item>

      <el-menu-item index="/admin/datasources">
        <el-icon><Connection /></el-icon>
        <template #title>数据源</template>
      </el-menu-item>

      <el-menu-item index="/admin/reports">
        <el-icon><Document /></el-icon>
        <template #title>报表管理</template>
      </el-menu-item>

      <el-menu-item index="/admin/etl/jobs">
        <el-icon><Timer /></el-icon>
        <template #title>ETL 任务</template>
      </el-menu-item>

      <el-menu-item index="/admin/monitor/system">
        <el-icon><Warning /></el-icon>
        <template #title>系统日志</template>
      </el-menu-item>
    </el-menu>

    <!-- 底部用户信息 -->
    <div class="sidebar-footer">
      <el-dropdown trigger="click" placement="top" v-if="!isCollapsed">
        <div class="user-info">
          <el-avatar :size="36" :icon="User" />
          <div class="user-details">
            <span class="username">{{ username }}</span>
            <span class="user-role">管理员</span>
          </div>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>
              <el-icon><Setting /></el-icon>
              个人设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- 折叠状态下的用户头像 -->
      <el-tooltip content="退出登录" placement="right" v-else>
        <el-button class="logout-btn" @click="handleLogout" link>
          <el-avatar :size="36" :icon="User" />
        </el-button>
      </el-tooltip>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'

// Element Plus Icons
import {
  DataLine, House, DataBoard, ChatDotRound, Refresh,
  Monitor, User, UserFilled, Connection, Document, Timer, Warning,
  Fold, Expand, SwitchButton, Setting
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const isCollapsed = ref(false)
const username = computed(() => localStorage.getItem('username') || '管理员')
const activeMenu = computed(() => route.path)

// 切换折叠状态
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/login')
  } catch {
    // 取消退出
  }
}

// 监听路由变化，确保菜单高亮正确
watch(() => route.path, () => {
  // 路由变化时自动更新 activeMenu
})
</script>

<style scoped>
/* ========================================
   侧边栏 - 专业深色主题
   ======================================== */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: linear-gradient(180deg, var(--slate-900) 0%, var(--slate-800) 100%);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-slow) var(--transition-cubic);
  z-index: var(--z-fixed);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.12);
}

.sidebar-collapsed {
  width: var(--sidebar-collapsed-width);
}

/* 侧边栏头部 */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-5) var(--spacing-4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  height: var(--header-height);
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  overflow: hidden;
}

.logo-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border-radius: var(--radius-lg);
  color: white;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.logo-text {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: white;
  white-space: nowrap;
  letter-spacing: 0.5px;
  transition: opacity var(--transition-slow) var(--transition-cubic);
}

.collapse-btn {
  color: var(--slate-400);
  transition: all var(--transition-fast) var(--transition-cubic);
  padding: var(--spacing-2);
  border-radius: var(--radius-md);
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

/* 导航菜单 */
.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  border-right: none;
  background: transparent;
  padding: var(--spacing-3) var(--spacing-2);
}

.sidebar-menu::-webkit-scrollbar {
  width: 4px;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-full);
}

/* 菜单分组 */
.menu-section {
  padding: var(--spacing-3) var(--spacing-3) var(--spacing-2);
}

.menu-section-title {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--slate-500);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* 菜单项 */
.sidebar-menu :deep(.el-menu-item) {
  height: 44px;
  margin: var(--spacing-1) 0;
  border-radius: var(--radius-md);
  color: var(--slate-400);
  transition: all var(--transition-fast) var(--transition-cubic);
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.sidebar-menu :deep(.el-menu-item .el-icon) {
  width: 20px;
  height: 20px;
  margin-right: var(--spacing-3);
  font-size: 18px;
}

/* 分隔线 */
.el-divider {
  margin: var(--spacing-3) var(--spacing-2);
  background: rgba(255, 255, 255, 0.08);
}

/* 底部用户信息 */
.sidebar-footer {
  padding: var(--spacing-4);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all var(--transition-fast) var(--transition-cubic);
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.1);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.username {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: white;
}

.user-role {
  font-size: var(--text-xs);
  color: var(--slate-500);
}

.logout-btn {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: var(--spacing-2);
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
  }

  .sidebar.mobile-visible {
    transform: translateX(0);
  }
}
</style>
