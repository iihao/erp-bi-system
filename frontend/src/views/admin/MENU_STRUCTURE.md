# 后台菜单重新分类排布方案

## 📋 菜单结构（新版）

### 1️⃣ 管理驾驶舱
- **管理驾驶舱** `/admin/dashboard`
  - 📊 系统 KPI 统计
  - 📈 数据趋势图表
  - 🔥 查询热度排行

---

### 2️⃣ 数据仓库
- **数仓概览** `/admin/warehouse/overview`
  - 数仓分层架构图
  - 各层表统计
  - 数据更新状态

- **ODS 层数据** `/admin/warehouse/ods`
  - ods_room 房源明细
  - ods_trade 销售明细
  - ods_payment 回款明细
  - ods_pay 付款登记
  - ods_contract 合同表

- **DWD 层明细** `/admin/warehouse/dwd`
  - dwd_room_detail 房源明细
  - dwd_trade_detail 销售明细
  - dwd_payment_detail 回款明细
  - dwd_contract_detail 合同明细

- **DWS 层聚合** `/admin/warehouse/dws`
  - dws_sales_payment_fact 销售回款事实表
  - dws_sales_cost_fact 成本费用事实表
  - dim_project 项目维度
  - dim_date 时间维度
  - dim_account 科目维度

- **ADS 层报表** `/admin/warehouse/ads`
  - ads_sales_dashboard 营销驾驶舱
  - ads_finance_dashboard 财务驾驶舱
  - ads_group_sales_report 集团销售目标
  - ads_project_cost_report 项目成本

---

### 3️⃣ ETL 调度
- **任务管理** `/admin/etl/tasks`
  - ETL 任务列表
  - 任务状态监控
  - 手动触发执行

- **调度配置** `/admin/etl/schedules`
  - Cron 表达式配置
  - 调度计划管理
  - 任务启停控制

- **执行日志** `/admin/etl/logs`
  - ETL 执行历史
  - 错误日志查看
  - 执行时长统计

- **监控告警** `/admin/etl/monitor`
  - 数据新鲜度监控
  - 数据质量检查
  - 告警配置管理

---

### 4️⃣ BI 报表
- **报表设计器** `/admin/bi/dashboard`
  - 可视化报表设计
  - 组件拖拽配置
  - 报表预览发布

- **我的报表** `/admin/bi/reports`
  - 已保存报表列表
  - 报表收藏管理
  - 报表分享

- **Metabase BI** `/admin/bi/metabase` 🔗
  - 外部链接：http://localhost:3001
  - 专业 BI 分析工具

---

### 5️⃣ 数据源管理
- **数据源配置** `/admin/datasources`
  - MySQL 连接配置
  - SQLite 连接配置
  - SAP ERP 连接
  - Excel 数据导入

- **标准 SQL 库** `/admin/standard-sql`
  - 常用 SQL 模板
  - 存储过程管理
  - 函数库管理

---

### 6️⃣ AI 智能分析
- **AI 问数** `/admin/ai-query`
  - 自然语言查询
  - SQL 自动生成
  - 数据智能分析

- **问数记录** `/admin/ai-records`
  - 历史查询记录
  - 热门问题分析
  - 查询优化建议

---

### 7️⃣ 系统管理
- **用户管理** `/admin/users`
  - 用户列表
  - 用户 CRUD
  - 密码重置
  - 状态切换

- **角色管理** `/admin/roles`
  - 角色列表
  - 权限配置
  - 角色分配

- **权限管理** `/admin/permissions`
  - 权限列表
  - 权限分配
  - 行级权限

- **系统日志** `/admin/logs`
  - 操作日志
  - 登录日志
  - 异常日志

---

### 🏠 快捷入口
- **地产 ERP** `/admin/realestate`
- **返回前台** `/dashboard`

---

## 🎨 菜单图标方案

| 菜单项 | 图标 | 颜色 |
|--------|------|------|
| 管理驾驶舱 | 📊 仪表盘 | #3b82f6 蓝色 |
| 数据仓库 | 🗄️ 数据库 | #10b981 绿色 |
| ETL 调度 | ⚙️ 齿轮 | #f59e0b 橙色 |
| BI 报表 | 📈 图表 | #8b5cf6 紫色 |
| 数据源管理 | 🔌 连接 | #06b6d4 青色 |
| AI 智能分析 | 🤖 机器人 | #ec4899 粉色 |
| 系统管理 | 🔐 锁 | #64748b 灰色 |

---

## 📱 响应式设计

- **桌面端** (>1024px): 完整侧边栏菜单
- **平板端** (768-1024px): 可折叠侧边栏
- **移动端** (<768px): 汉堡菜单 + 遮罩层

---

## 🔗 路由配置

```javascript
// router/index.js
const routes = [
  {
    path: '/admin',
    component: AdminLayout,
    children: [
      // 管理驾驶舱
      { path: 'dashboard', component: Dashboard },
      
      // 数据仓库
      { path: 'warehouse/overview', component: WarehouseOverview },
      { path: 'warehouse/ods', component: ODSData },
      { path: 'warehouse/dwd', component: DWDData },
      { path: 'warehouse/dws', component: DWSData },
      { path: 'warehouse/ads', component: ADSData },
      
      // ETL 调度
      { path: 'etl/tasks', component: ETLTasks },
      { path: 'etl/schedules', component: ETLSchedules },
      { path: 'etl/logs', component: ETLLogs },
      { path: 'etl/monitor', component: ETLMonitor },
      
      // BI 报表
      { path: 'bi/dashboard', component: ReportDesigner },
      { path: 'bi/reports', component: ReportList },
      { path: 'bi/metabase', component: MetabaseLink },
      
      // 数据源管理
      { path: 'datasources', component: Datasources },
      { path: 'standard-sql', component: StandardSQL },
      
      // AI 智能分析
      { path: 'ai-query', component: AIQuery },
      { path: 'ai-records', component: AIRecords },
      
      // 系统管理
      { path: 'users', component: Users },
      { path: 'roles', component: Roles },
      { path: 'permissions', component: Permissions },
      { path: 'logs', component: SystemLogs }
    ]
  }
]
```

---

## ✅ 菜单优化亮点

1. **逻辑清晰**: 按数据流向组织（数据源→数仓→ETL→BI）
2. **功能聚合**: 相关功能放在同一菜单下
3. **快捷入口**: 常用功能一级菜单直达
4. **视觉识别**: 每个菜单有独特图标和颜色
5. **可扩展**: 预留扩展空间，方便后续添加

---

**更新时间**: 2026-03-19
