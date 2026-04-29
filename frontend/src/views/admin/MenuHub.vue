<template>
  <div class="menu-hub">
    <!-- 页面头部 -->
    <div class="hub-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon :size="28"><Grid /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="hub-title">后台功能导航</h1>
          <p class="hub-subtitle">快速访问所有功能模块</p>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-label">功能模块</span>
          <span class="stat-value">6</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-label">子功能</span>
          <span class="stat-value">28</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-label">运行状态</span>
          <span class="stat-badge"><el-icon><CircleCheck /></el-icon> 正常</span>
        </div>
      </div>
    </div>

    <!-- 常用功能快捷入口 -->
    <div class="quick-access">
      <h2 class="section-title">
        <el-icon class="title-icon"><Star /></el-icon>
        常用功能
      </h2>
      <div class="quick-grid">
        <router-link to="/admin/dashboard" class="quick-card">
          <div class="card-accent primary"></div>
          <div class="card-icon-wrap primary-bg">
            <el-icon :size="24"><DataAnalysis /></el-icon>
          </div>
          <div class="card-info">
            <h3>管理驾驶舱</h3>
            <p>系统 KPI 统计</p>
          </div>
        </router-link>
        <router-link to="/admin/datasources" class="quick-card">
          <div class="card-accent cyan"></div>
          <div class="card-icon-wrap cyan-bg">
            <el-icon :size="24"><Connection /></el-icon>
          </div>
          <div class="card-info">
            <h3>数据源管理</h3>
            <p>数据源配置与维护</p>
          </div>
        </router-link>
        <router-link to="/admin/etl/tasks" class="quick-card">
          <div class="card-accent warning"></div>
          <div class="card-icon-wrap warning-bg">
            <el-icon :size="24"><Timer /></el-icon>
          </div>
          <div class="card-info">
            <h3>ETL 任务</h3>
            <p>调度与执行管理</p>
          </div>
        </router-link>
        <router-link to="/admin/reports/designer-pro" class="quick-card">
          <div class="card-accent info"></div>
          <div class="card-icon-wrap info-bg">
            <el-icon :size="24"><TrendCharts /></el-icon>
          </div>
          <div class="card-info">
            <h3>报表设计器</h3>
            <p>可视化报表设计</p>
          </div>
        </router-link>
        <a :href="metabaseUrl" target="_blank" rel="noopener noreferrer" class="quick-card">
          <div class="card-accent purple"></div>
          <div class="card-icon-wrap purple-bg">
            <el-icon :size="24"><Link /></el-icon>
          </div>
          <div class="card-info">
            <h3>Metabase BI</h3>
            <p>专业 BI 分析</p>
          </div>
        </a>
        <router-link to="/admin/ai-query-simple" class="quick-card">
          <div class="card-accent pink"></div>
          <div class="card-icon-wrap pink-bg">
            <el-icon :size="24"><ChatDotRound /></el-icon>
          </div>
          <div class="card-info">
            <h3>AI 问数</h3>
            <p>自然语言查询</p>
          </div>
        </router-link>
        <router-link to="/admin/ai-report" class="quick-card">
          <div class="card-accent info"></div>
          <div class="card-icon-wrap info-bg">
            <el-icon :size="24"><Files /></el-icon>
          </div>
          <div class="card-info">
            <h3>AI 智能报表</h3>
            <p>自然语言转报表</p>
          </div>
        </router-link>
      </div>
    </div>

    <!-- 功能模块详细列表 -->
    <div class="modules-section">
      <h2 class="section-title">
        <el-icon class="title-icon"><Menu /></el-icon>
        功能模块
      </h2>
      <div class="modules-grid">
        <!-- 系统管理 -->
        <div class="module-card">
          <div class="module-header">
            <div class="module-icon-wrap success-bg">
              <el-icon :size="20"><Setting /></el-icon>
            </div>
            <h2>系统管理</h2>
            <el-tag size="small" effect="plain">4 项</el-tag>
          </div>
          <div class="module-list">
            <router-link to="/admin/users" class="module-link">
              <el-icon class="link-icon"><User /></el-icon>
              <span>用户管理</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/roles" class="module-link">
              <el-icon class="link-icon"><Avatar /></el-icon>
              <span>角色管理</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/permissions" class="module-link">
              <el-icon class="link-icon"><Key /></el-icon>
              <span>权限管理</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/system/update-logs" class="module-link">
              <el-icon class="link-icon"><DocumentCopy /></el-icon>
              <span>更新日志</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
          </div>
        </div>

        <!-- 数据源管理 -->
        <div class="module-card">
          <div class="module-header">
            <div class="module-icon-wrap cyan-bg">
              <el-icon :size="20"><Connection /></el-icon>
            </div>
            <h2>数据源管理</h2>
            <el-tag size="small" effect="plain">2 项</el-tag>
          </div>
          <div class="module-list">
            <router-link to="/admin/datasources" class="module-link">
              <el-icon class="link-icon"><Coin /></el-icon>
              <span>数据源配置</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/standard-sql" class="module-link">
              <el-icon class="link-icon"><Notebook /></el-icon>
              <span>标准 SQL 库</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
          </div>
        </div>

        <!-- ETL 开发 -->
        <div class="module-card">
          <div class="module-header">
            <div class="module-icon-wrap warning-bg">
              <el-icon :size="20"><Timer /></el-icon>
            </div>
            <h2>ETL 开发</h2>
            <el-tag size="small" effect="plain">7 项</el-tag>
          </div>
          <div class="module-list">
            <router-link to="/admin/etl/tasks" class="module-link">
              <el-icon class="link-icon"><List /></el-icon>
              <span>任务管理</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/etl/jobs" class="module-link">
              <el-icon class="link-icon"><Grid /></el-icon>
              <span>作业定义</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/etl/schedules" class="module-link">
              <el-icon class="link-icon"><Calendar /></el-icon>
              <span>调度配置</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/etl/development" class="module-link">
              <el-icon class="link-icon"><EditPen /></el-icon>
              <span>数据开发</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/etl/editor" class="module-link">
              <el-icon class="link-icon"><Edit /></el-icon>
              <span>ETL 编辑器</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/etl/logs" class="module-link">
              <el-icon class="link-icon"><Document /></el-icon>
              <span>执行日志</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/etl/monitor" class="module-link">
              <el-icon class="link-icon"><Monitor /></el-icon>
              <span>监控告警</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
          </div>
        </div>

        <!-- 报表管理 -->
        <div class="module-card">
          <div class="module-header">
            <div class="module-icon-wrap info-bg">
              <el-icon :size="20"><TrendCharts /></el-icon>
            </div>
            <h2>报表管理</h2>
            <el-tag size="small" effect="plain">6 项</el-tag>
          </div>
          <div class="module-list">
            <router-link to="/admin/reports" class="module-link">
              <el-icon class="link-icon"><Files /></el-icon>
              <span>报表列表</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/reports/designer" class="module-link">
              <el-icon class="link-icon"><Brush /></el-icon>
              <span>报表设计器</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/reports/designer-pro" class="module-link">
              <el-icon class="link-icon"><MagicStick /></el-icon>
              <span>高级报表设计器</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/bi/dashboard" class="module-link">
              <el-icon class="link-icon"><DataAnalysis /></el-icon>
              <span>可视化报表</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/bi/reports" class="module-link">
              <el-icon class="link-icon"><Notebook /></el-icon>
              <span>我的报表</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <a :href="metabaseUrl" target="_blank" rel="noopener noreferrer" class="module-link">
              <el-icon class="link-icon"><Link /></el-icon>
              <span>Metabase BI</span>
              <el-icon class="link-arrow"><TopRight /></el-icon>
            </a>
          </div>
        </div>

        <!-- AI 智能分析 -->
        <div class="module-card">
          <div class="module-header">
            <div class="module-icon-wrap pink-bg">
              <el-icon :size="20"><ChatDotRound /></el-icon>
            </div>
            <h2>AI 智能分析</h2>
            <el-tag size="small" effect="plain">5 项</el-tag>
          </div>
          <div class="module-list">
            <router-link to="/admin/ai-query" class="module-link">
              <el-icon class="link-icon"><Setting /></el-icon>
              <span>AI 配置中心</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/ai-query-simple" class="module-link">
              <el-icon class="link-icon"><ChatLineSquare /></el-icon>
              <span>AI 问数（优化版）</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/ai-enhanced" class="module-link">
              <el-icon class="link-icon"><MagicStick /></el-icon>
              <span>智能问数</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/ai-report" class="module-link">
              <el-icon class="link-icon"><Files /></el-icon>
              <span>AI 智能报表</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/ai-records" class="module-link">
              <el-icon class="link-icon"><Document /></el-icon>
              <span>问数记录</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
          </div>
        </div>

        <!-- 系统监控 -->
        <div class="module-card">
          <div class="module-header">
            <div class="module-icon-wrap danger-bg">
              <el-icon :size="20"><Monitor /></el-icon>
            </div>
            <h2>系统监控</h2>
            <el-tag size="small" effect="plain">2 项</el-tag>
          </div>
          <div class="module-list">
            <router-link to="/admin/monitor/system" class="module-link">
              <el-icon class="link-icon"><Cpu /></el-icon>
              <span>系统信息</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
            <router-link to="/admin/monitor/logs" class="module-link">
              <el-icon class="link-icon"><Tickets /></el-icon>
              <span>系统日志</span>
              <el-icon class="link-arrow"><ArrowRight /></el-icon>
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h2 class="section-title">
        <el-icon class="title-icon"><Operation /></el-icon>
        快捷操作
      </h2>
      <div class="action-bar">
        <el-button type="primary" @click="runETL">
          <el-icon><CaretRight /></el-icon>
          执行 ETL
        </el-button>
        <el-button type="success" @click="openMetabase">
          <el-icon><Link /></el-icon>
          打开 Metabase
        </el-button>
        <el-button type="warning" @click="viewLogs">
          <el-icon><Tickets /></el-icon>
          查看日志
        </el-button>
        <el-button @click="checkStatus">
          <el-icon><CircleCheck /></el-icon>
          系统检查
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getMetabaseUrl } from '@/utils/metabase'

// Element Plus Icons
import {
  Grid, Star, DataAnalysis, Connection, Timer, TrendCharts,
  Link, ChatDotRound, Setting, User, Avatar, Key, DocumentCopy,
  Coin, Notebook, List, EditPen, Edit, Bell, Files, Brush,
  ChatLineSquare, MagicStick, Document, Monitor, Cpu, Tickets,
  Operation, CaretRight, CircleCheck, ArrowRight, TopRight, Menu, Calendar
} from '@element-plus/icons-vue'

const router = useRouter()
const metabaseUrl = getMetabaseUrl()

const runETL = () => {
  router.push('/admin/etl/tasks')
}

const openMetabase = () => {
  window.open(metabaseUrl, '_blank', 'noopener,noreferrer')
}

const viewLogs = () => {
  router.push('/admin/etl/logs')
}

const checkStatus = () => {
  ElMessage.success('系统运行正常')
}
</script>

<style scoped>
.menu-hub {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面头部 */
.hub-header {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border-radius: 12px;
  padding: 28px 32px;
  margin-bottom: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 14px;
  backdrop-filter: blur(8px);
}

.header-text .hub-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 4px 0;
  letter-spacing: 0.5px;
}

.header-text .hub-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
}

.stat-divider {
  width: 1px;
  height: 36px;
  background: rgba(255, 255, 255, 0.2);
}

.stat-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 600;
  color: #a7f3d0;
}

/* 常用功能 */
.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 20px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  color: #3b82f6;
}

.quick-access {
  margin-bottom: 36px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.quick-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px;
  background: #fff;
  border-radius: 12px;
  text-decoration: none;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.card-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.card-accent.primary { background: #2563eb; }
.card-accent.cyan { background: #0ea5e9; }
.card-accent.warning { background: #d97706; }
.card-accent.info { background: #0ea5e9; }
.card-accent.purple { background: #7c3aed; }
.card-accent.pink { background: #db2777; }

.quick-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  border-color: transparent;
}

.card-icon-wrap {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  margin-bottom: 14px;
  color: #fff;
}

.primary-bg { background: #2563eb; }
.cyan-bg { background: #0ea5e9; }
.warning-bg { background: #d97706; }
.info-bg { background: #0ea5e9; }
.purple-bg { background: #7c3aed; }
.pink-bg { background: #db2777; }

.card-info h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 4px 0;
}

.card-info p {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
}

/* 功能模块 */
.modules-section {
  margin-bottom: 36px;
}

.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.module-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.module-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  border-color: #cbd5e1;
}

.module-header {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.module-icon-wrap {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  color: #fff;
  flex-shrink: 0;
}

.success-bg { background: #22c55e; }
.danger-bg { background: #ef4444; }

.module-header h2 {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  flex: 1;
}

.module-list {
  padding: 8px 12px;
}

.module-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: #475569;
  text-decoration: none;
  font-size: 14px;
  border-radius: 8px;
  transition: all 0.2s;
}

.module-link:hover {
  background: #f1f5f9;
  color: #3b82f6;
}

.link-icon {
  color: #94a3b8;
  flex-shrink: 0;
}

.module-link:hover .link-icon {
  color: #3b82f6;
}

.link-arrow {
  margin-left: auto;
  color: #cbd5e1;
  transition: all 0.2s;
}

.module-link:hover .link-arrow {
  color: #3b82f6;
  transform: translateX(2px);
}

/* 快捷操作 */
.quick-actions {
  margin-bottom: 36px;
}

.action-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 响应式 */
@media (max-width: 768px) {
  .menu-hub {
    padding: 16px;
  }

  .hub-header {
    flex-direction: column;
    gap: 20px;
    padding: 24px;
  }

  .header-stats {
    width: 100%;
    justify-content: space-around;
  }

  .hub-title {
    font-size: 22px;
  }

  .quick-grid,
  .modules-grid {
    grid-template-columns: 1fr;
  }

  .action-bar {
    flex-direction: column;
  }

  .action-bar :deep(.el-button) {
    width: 100%;
  }
}
</style>
