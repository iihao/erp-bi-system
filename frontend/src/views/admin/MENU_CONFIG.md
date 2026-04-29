# 后台菜单配置指南

## 📋 菜单结构总览

```
管理后台
├── 🗂️ 后台功能导航（新增）    /admin/menu-hub
├── 📊 管理驾驶舱             /admin/dashboard
├── 🗄️ 数据仓库
│   ├── 数仓概览             /admin/warehouse/overview
│   ├── ODS 层数据            /admin/warehouse/ods
│   ├── DWD 层明细            /admin/warehouse/dwd
│   ├── DWS 层聚合            /admin/warehouse/dws
│   └── ADS 层报表            /admin/warehouse/ads
├── ⚙️ ETL 调度
│   ├── 任务管理             /admin/etl/tasks
│   ├── 调度配置             /admin/etl/schedules
│   ├── 执行日志             /admin/etl/logs
│   └── 监控告警             /admin/etl/monitor
├── 📈 BI 报表
│   ├── 报表设计器            /admin/bi/dashboard
│   ├── 我的报表             /admin/bi/reports
│   └── Metabase BI 🔗       http://localhost:3001
├── 🔌 数据源管理
│   ├── 数据源配置            /admin/datasources
│   └── 标准 SQL 库            /admin/standard-sql
├── 🤖 AI 智能分析
│   ├── AI 问数               /admin/ai-query
│   └── 问数记录             /admin/ai-records
└── 🔐 系统管理
    ├── 用户管理             /admin/users
    ├── 角色管理             /admin/roles
    ├── 权限管理             /admin/permissions
    └── 系统日志             /admin/logs
```

---

## 🆕 新增页面

### 1. 后台功能导航中心

**文件**: `frontend/src/views/admin/MenuHub.vue`

**路由**: `/admin/menu-hub`

**功能**:
- 所有功能模块的快速导航
- 数仓数据状态展示
- 常用功能快捷入口
- 快捷操作按钮

**访问方式**:
- 直接访问：http://localhost:3000/admin/menu-hub
- 从左侧菜单点击"后台功能导航"

---

## 🔧 路由配置

### 添加新路由

编辑 `frontend/src/router/index.js`:

```javascript
{
  path: '/admin',
  component: AdminLayout,
  children: [
    // 新增：功能导航中心
    { 
      path: 'menu-hub', 
      name: 'MenuHub',
      component: () => import('@/views/admin/MenuHub.vue'),
      meta: { title: '功能导航', icon: '🗂️' }
    },
    
    // 管理驾驶舱
    { 
      path: 'dashboard', 
      name: 'AdminDashboard',
      component: () => import('@/views/admin/Dashboard.vue'),
      meta: { title: '管理驾驶舱', icon: '📊' }
    },
    
    // 数据仓库
    {
      path: 'warehouse',
      name: 'Warehouse',
      meta: { title: '数据仓库', icon: '🗄️' },
      children: [
        { path: 'overview', component: () => import('@/views/warehouse/Overview.vue') },
        { path: 'ods', component: () => import('@/views/warehouse/ODSData.vue') },
        { path: 'dwd', component: () => import('@/views/warehouse/DWDData.vue') },
        { path: 'dws', component: () => import('@/views/warehouse/DWSData.vue') },
        { path: 'ads', component: () => import('@/views/warehouse/ADSData.vue') }
      ]
    },
    
    // ETL 调度
    {
      path: 'etl',
      name: 'ETL',
      meta: { title: 'ETL 调度', icon: '⚙️' },
      children: [
        { path: 'tasks', component: () => import('@/views/etl/Tasks.vue') },
        { path: 'schedules', component: () => import('@/views/etl/Schedules.vue') },
        { path: 'logs', component: () => import('@/views/etl/Logs.vue') },
        { path: 'monitor', component: () => import('@/views/etl/Monitor.vue') }
      ]
    },
    
    // BI 报表
    {
      path: 'bi',
      name: 'BI',
      meta: { title: 'BI 报表', icon: '📈' },
      children: [
        { path: 'dashboard', component: () => import('@/views/bi/ReportDesigner.vue') },
        { path: 'reports', component: () => import('@/views/bi/ReportList.vue') },
        { path: 'metabase', component: () => import('@/views/bi/MetabaseLink.vue') }
      ]
    },
    
    // ... 其他路由
  ]
}
```

---

## 📱 左侧菜单更新

### 更新 Layout.vue 菜单

编辑 `frontend/src/views/admin/Layout.vue`:

1. **添加功能导航入口**（放在最前面）
```vue
<el-menu-item index="/admin/menu-hub">
  <span class="menu-emoji">🗂️</span>
  <span>功能导航</span>
</el-menu-item>
```

2. **更新菜单结构**（参考 MENU_STRUCTURE.md）

---

## 🎨 菜单图标方案

| 菜单项 | Emoji | SVG 图标 | 颜色 |
|--------|-------|---------|------|
| 功能导航 | 🗂️ | `<svg>...</svg>` | #3b82f6 |
| 管理驾驶舱 | 📊 | `<svg>...</svg>` | #3b82f6 |
| 数据仓库 | 🗄️ | `<svg>...</svg>` | #10b981 |
| ETL 调度 | ⚙️ | `<svg>...</svg>` | #f59e0b |
| BI 报表 | 📈 | `<svg>...</svg>` | #8b5cf6 |
| 数据源管理 | 🔌 | `<svg>...</svg>` | #06b6d4 |
| AI 智能分析 | 🤖 | `<svg>...</svg>` | #ec4899 |
| 系统管理 | 🔐 | `<svg>...</svg>` | #64748b |

---

## 🔗 外部链接

### Metabase BI

**配置方式 1**: 新窗口打开
```vue
<el-menu-item index="/admin/bi/metabase" @click="openMetabase">
  <svg class="menu-icon">...</svg>
  <span>Metabase BI</span>
</el-menu-item>

<script setup>
const openMetabase = () => {
  window.open('http://localhost:3001', '_blank')
}
</script>
```

**配置方式 2**: iframe 嵌入
```vue
<template>
  <div class="metabase-frame">
    <iframe src="http://localhost:3001" frameborder="0"></iframe>
  </div>
</template>

<style scoped>
.metabase-frame {
  width: 100%;
  height: calc(100vh - 100px);
}
</style>
```

---

## 📊 数仓数据展示

### API 接口

```javascript
// 获取数仓数据统计
GET /api/admin/warehouse/stats

// 响应示例
{
  "ods": { tables: 9, records: 29 },
  "dwd": { tables: 7, records: 17 },
  "dws": { tables: 5, records: 5 },
  "ads": { tables: 7, records: 4 }
}
```

### 数据新鲜度

```javascript
// 获取数据更新日期
GET /api/admin/warehouse/freshness

// 响应示例
{
  "last_update": "2026-03-19 05:00:00",
  "next_update": "2026-03-20 02:00:00",
  "status": "normal"
}
```

---

## ✅ 验证步骤

### 1. 路由测试

```bash
# 访问功能导航中心
http://localhost:3000/admin/menu-hub

# 访问各功能模块
http://localhost:3000/admin/warehouse/overview
http://localhost:3000/admin/etl/tasks
http://localhost:3000/admin/bi/dashboard
```

### 2. 菜单测试

- [ ] 左侧菜单展开/收起正常
- [ ] 子菜单展开正常
- [ ] 路由跳转正常
- [ ] 外部链接正常打开

### 3. 响应式测试

- [ ] 桌面端显示正常
- [ ] 平板端显示正常
- [ ] 移动端显示正常

---

## 🎯 菜单优化亮点

1. **逻辑清晰**: 按数据流向组织（数据源→数仓→ETL→BI）
2. **快捷入口**: 功能导航中心一键直达
3. **视觉识别**: 每个菜单有独特图标和颜色
4. **状态展示**: 数仓数据状态一目了然
5. **可扩展**: 预留扩展空间，方便后续添加

---

## 📝 待开发页面

以下页面需要后续开发：

- [ ] `/admin/warehouse/overview` - 数仓概览
- [ ] `/admin/warehouse/ods` - ODS 层数据
- [ ] `/admin/warehouse/dwd` - DWD 层明细
- [ ] `/admin/warehouse/dws` - DWS 层聚合
- [ ] `/admin/warehouse/ads` - ADS 层报表
- [ ] `/admin/etl/tasks` - ETL 任务管理
- [ ] `/admin/etl/schedules` - ETL 调度配置
- [ ] `/admin/etl/logs` - ETL 执行日志
- [ ] `/admin/etl/monitor` - ETL 监控告警
- [ ] `/admin/bi/reports` - 我的报表

**临时方案**: 这些页面可以暂时显示"功能开发中"提示，或跳转到功能导航中心。

---

**更新时间**: 2026-03-19  
**版本**: v1.0.0
