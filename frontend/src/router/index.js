import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/',
    redirect: '/portal/dashboard'
  },
  {
    path: '/data',
    name: 'DataPreview',
    component: () => import('@/views/portal/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        component: () => import('@/views/data/TablePreview.vue')
      }
    ]
  },
  {
    path: '/etl',
    name: 'ETLTasks',
    component: () => import('@/views/portal/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        component: () => import('@/views/etl/TaskList.vue')
      }
    ]
  },
  // 后台管理路由 - 使用独立的左右布局
  {
    path: '/admin',
    component: () => import('@/views/admin/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/admin/menu-hub'
      },
      {
        path: 'menu-hub',
        name: 'MenuHub',
        component: () => import('@/views/admin/MenuHub.vue'),
        meta: { title: '功能导航' }
      },
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '管理驾驶舱' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/Users.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'roles',
        name: 'AdminRoles',
        component: () => import('@/views/admin/Roles.vue'),
        meta: { title: '角色管理' }
      },
      {
        path: 'permissions',
        name: 'AdminPermissions',
        component: () => import('@/views/admin/Permissions.vue'),
        meta: { title: '权限管理' }
      },
      {
        path: 'reports',
        name: 'AdminReports',
        component: () => import('@/views/admin/Reports.vue'),
        meta: { title: '报表列表' }
      },
      {
        path: 'reports/designer',
        name: 'ReportDesigner',
        component: () => import('@/views/admin/ReportDesigner.vue'),
        meta: { title: '报表设计器' }
      },
      {
        path: 'reports/designer-pro',
        name: 'ReportDesignerPro',
        component: () => import('@/views/admin/ReportDesignerPro.vue'),
        meta: { title: '高级报表设计器' }
      },
      {
        path: 'etl/jobs',
        name: 'AdminEtlJobs',
        component: () => import('@/views/admin/EtlJobs.vue'),
        meta: { title: 'ETL 作业定义' }
      },
      {
        path: 'etl/tasks',
        name: 'AdminEtlTasks',
        component: () => import('@/views/admin/EtlTasks.vue'),
        meta: { title: 'ETL 任务管理' }
      },
      {
        path: 'etl/schedules',
        name: 'AdminEtlSchedules',
        component: () => import('@/views/admin/EtlSchedules.vue'),
        meta: { title: 'ETL 调度配置' }
      },
      {
        path: 'etl/development',
        name: 'AdminEtlDevelopment',
        component: () => import('@/views/admin/EtlDevelopment.vue'),
        meta: { title: 'ETL 数据开发' }
      },
      {
        path: 'etl/editor',
        name: 'AdminEtlEditor',
        component: () => import('@/views/admin/EtlEditor.vue'),
        meta: { title: 'ETL 编辑器' }
      },
      {
        path: 'etl/logs',
        name: 'AdminEtlLogs',
        component: () => import('@/views/admin/EtlLogs.vue'),
        meta: { title: 'ETL 执行日志' }
      },
      {
        path: 'etl/monitor',
        name: 'AdminEtlMonitor',
        component: () => import('@/views/admin/Monitor.vue'),
        meta: { title: 'ETL 监控告警' }
      },
      {
        path: 'ai-query',
        name: 'AdminAIQuery',
        component: () => import('@/views/admin/AIQuery.vue'),
        meta: { title: 'AI 配置中心' }
      },
      {
        path: 'ai-enhanced',
        name: 'AIEnhancedQuery',
        component: () => import('@/views/admin/AIEnhancedQuery.vue'),
        meta: { title: '智能问数' }
      },
      {
        path: 'ai-report',
        name: 'AdminAIReport',
        component: () => import('@/views/admin/AIReport.vue'),
        meta: { title: 'AI 智能报表' }
      },
      {
        path: 'ai-records',
        name: 'AdminAIRecords',
        component: () => import('@/views/admin/AIRecords.vue'),
        meta: { title: '问数记录' }
      },
      {
        path: 'standard-sql',
        name: 'AdminStandardSql',
        component: () => import('@/views/admin/StandardSqlLibrary.vue'),
        meta: { title: '标准 SQL 库' }
      },
      {
        path: 'datasources',
        name: 'AdminDatasources',
        component: () => import('@/views/admin/Datasources.vue'),
        meta: { title: '数据源管理' }
      },
      {
        path: 'datasources/:id/preview',
        name: 'AdminDatasourcePreview',
        component: () => import('@/views/admin/DatasourcePreview.vue'),
        meta: { title: '数据源预览' }
      },
      {
        path: 'monitor/system',
        name: 'AdminMonitorSystem',
        component: () => import('@/views/admin/Monitor.vue'),
        meta: { title: '系统监控' }
      },
      {
        path: 'monitor/logs',
        name: 'AdminMonitorLogs',
        component: () => import('@/views/admin/Monitor.vue'),
        meta: { title: '系统日志' }
      },
      {
        path: 'monitor/ai-records',
        name: 'AdminMonitorAIRecords',
        component: () => import('@/views/admin/AIRecords.vue'),
        meta: { title: '问数记录' }
      },
      {
        path: 'system/update-logs',
        name: 'SystemUpdateLogs',
        component: () => import('@/views/admin/UpdateLogs.vue'),
        meta: { title: '更新日志' }
      },
      {
        path: 'system/ai-config',
        name: 'SystemAIConfig',
        component: () => import('@/views/admin/AIConfig.vue'),
        meta: { title: 'AI 配置' }
      },
      {
        path: 'test-buttons',
        name: 'TestButtons',
        component: () => import('@/views/admin/TestButtons.vue'),
        meta: { title: '按钮测试' }
      },
      {
        path: 'simple-test',
        name: 'SimpleTest',
        component: () => import('@/views/admin/SimpleTest.vue'),
        meta: { title: '简单测试' }
      },
      {
        path: 'ai-query-simple',
        name: 'AIQuerySimple',
        component: () => import('@/views/admin/AIQuerySimple.vue'),
        meta: { title: 'AI 问数（优化版）' }
      },
      // 数据仓库模块
      {
        path: 'warehouse/overview',
        name: 'WarehouseOverview',
        component: () => import('@/views/warehouse/Overview.vue'),
        meta: { title: '数仓概览' }
      },
      {
        path: 'warehouse/ods',
        name: 'WarehouseODS',
        component: () => import('@/views/warehouse/ODSData.vue'),
        meta: { title: 'ODS 层数据' }
      },
      {
        path: 'warehouse/dwd',
        name: 'WarehouseDWD',
        component: () => import('@/views/warehouse/DWDData.vue'),
        meta: { title: 'DWD 层明细' }
      },
      {
        path: 'warehouse/dws',
        name: 'WarehouseDWS',
        component: () => import('@/views/warehouse/DWSData.vue'),
        meta: { title: 'DWS 层聚合' }
      },
      {
        path: 'warehouse/ads',
        name: 'WarehouseADS',
        component: () => import('@/views/warehouse/ADSData.vue'),
        meta: { title: 'ADS 层报表' }
      },
      // ETL 调度模块
      {
        path: 'etl/tasks',
        name: 'ETLTasks',
        component: () => import('@/views/etl/Tasks.vue'),
        meta: { title: '任务管理' }
      },
      {
        path: 'etl/schedules',
        name: 'ETLSchedules',
        component: () => import('@/views/etl/Schedules.vue'),
        meta: { title: '调度配置' }
      },
      {
        path: 'etl/logs',
        name: 'ETLLogs',
        component: () => import('@/views/etl/Logs.vue'),
        meta: { title: '执行日志' }
      },
      {
        path: 'etl/monitor',
        name: 'ETLMonitor',
        component: () => import('@/views/etl/Monitor.vue'),
        meta: { title: '监控告警' }
      },
      // BI 报表模块
      {
        path: 'bi/dashboard',
        name: 'BIReportDesigner',
        component: () => import('@/views/bi/VisualReportDesigner.vue'),
        meta: { title: '报表设计器' }
      },
      {
        path: 'bi/reports',
        name: 'BIReportList',
        component: () => import('@/views/bi/ReportList.vue'),
        meta: { title: '我的报表' }
      },
      {
        path: 'bi/metabase',
        name: 'MetabaseLink',
        component: () => import('@/views/bi/MetabaseLink.vue'),
        meta: { title: 'Metabase BI', external: true }
      },
      // 个人主页
      {
        path: 'profile',
        name: 'AdminProfile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人主页' }
      },
      // 树洞功能
      {
        path: 'treehole',
        name: 'AdminTreehole',
        component: () => import('@/views/admin/Treehole.vue'),
        meta: { title: '树洞' }
      },
      // 发现页面
      {
        path: 'discovery',
        name: 'Discovery',
        component: () => import('@/views/admin/Discovery.vue'),
        meta: { title: '发现' }
      },
      // 消息功能
      {
        path: 'messages',
        name: 'AdminMessages',
        component: () => import('@/views/admin/Messages.vue'),
        meta: { title: '消息中心' }
      }
    ]
  },
  // 前台报表系统路由
  {
    path: '/portal/login',
    name: 'PortalLogin',
    component: () => import('@/views/portal/Login.vue')
  },
  {
    path: '/portal',
    component: () => import('@/views/portal/Layout.vue'),
    meta: { requiresPortalAuth: true },
    children: [
      {
        path: '',
        redirect: '/portal/dashboard'
      },
      {
        path: 'dashboard',
        name: 'PortalDashboard',
        component: () => import('@/views/portal/Dashboard.vue')
      },
      {
        path: 'reports',
        name: 'PortalReports',
        component: () => import('@/views/portal/Reports.vue')
      },
      {
        path: 'report-portal',
        name: 'ReportPortal',
        component: () => import('@/views/portal/ReportPortal.vue')
      },
      {
        path: 'report/:id',
        name: 'PortalReportDetail',
        component: () => import('@/views/portal/ReportDetail.vue')
      },
      {
        path: 'ai-query',
        name: 'PortalAIQuery',
        component: () => import('@/views/portal/AIQuery.vue')
      },
      {
        path: 'smart-report',
        name: 'PortalSmartReport',
        component: () => import('@/views/portal/SmartReport.vue'),
        meta: { title: '智能报表' }
      },
      {
        path: 'realestate',
        name: 'PortalRealEstate',
        component: () => import('@/views/portal/RealEstateDashboard.vue'),
        meta: { title: '地产经营看板' }
      },
      {
        path: 'ai-chat',
        name: 'PortalAIChat',
        component: () => import('@/views/AIChat.vue'),
        meta: { title: 'AI 对话' }
      }
    ]
  },
  // 个人主页路由（独立于 admin 和 portal）
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true, title: '个人主页' }
  },
  {
    path: '/profile/:userId',
    name: 'UserProfile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true, title: '个人主页' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/portal/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 简单的 JWT token 验证（检查过期时间）
const isTokenValid = (token) => {
  if (!token) return false
  try {
    // JWT token 格式：header.payload.signature
    const parts = token.split('.')
    if (parts.length !== 3) return false
    
    // 解码 payload（base64url 解码）
    const payload = parts[1]
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
    
    // 检查过期时间
    if (decoded.exp) {
      const now = Math.floor(Date.now() / 1000)
      if (decoded.exp < now) {
        return false
      }
    }
    return true
  } catch (e) {
    return false
  }
}

// 清除认证信息并跳转登录
const clearAuthAndRedirect = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('portal_token')
  // 强制跳转，不使用 router.push 避免路由守卫死循环
  window.location.href = '/login'
}

// 公开路由，无需登录即可访问
const PUBLIC_ROUTES = new Set(['/login', '/portal/login'])

router.beforeEach((to, from, next) => {
  // 统一使用 token 进行认证（门户和后台共用）
  const token = localStorage.getItem('token')
  const isLoginPage = PUBLIC_ROUTES.has(to.path)

  // 无 token 且不在登录页 → 强制跳转登录页（覆盖所有路由）
  if (!token && !isLoginPage) {
    console.warn('[路由守卫] 未登录，强制跳转登录页', { path: to.path })
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  // 有 token 但已过期 → 清除并跳转登录页
  if (token && !isTokenValid(token) && !isLoginPage) {
    console.warn('[路由守卫] Token 已过期，强制跳转登录页', { path: to.path })
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('portal_username')
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  // 检查是否需要认证（门户和后台都需要）
  const requiresAuth = to.meta.requiresAuth || to.meta.requiresPortalAuth

  if (requiresAuth && !isTokenValid(token)) {
    console.warn('[路由守卫] Token 失效，强制跳转登录页', { path: to.path })
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  // 如果已登录且访问登录页，重定向到前台门户
  if (isLoginPage && token && isTokenValid(token)) {
    next('/portal')
    return
  }

  next()
})

export default router
