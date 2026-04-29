# AI数据融合平台需求完成汇报

## 完成时间
2026 年 3 月 15 日

---

## 一、创建/修改的文件列表

### 1.1 新建文件

#### 前端文件
| 文件路径 | 说明 |
|---------|------|
| `frontend/src/views/admin/Dashboard.vue` | 后台管理仪表盘 - 系统概况页面 |
| `frontend/src/views/portal/AIQuery.vue` | 前台 AI 智能问数页面 |
| `frontend/src/views/admin/AIQuery.vue` | 后台 AI 配置管理页面 |
| `frontend/src/views/admin/AIRecords.vue` | 后台 AI 问数记录页面 |
| `docs/API.md` | API 接口文档 |

#### 后端文件
| 文件路径 | 说明 |
|---------|------|
| `backend/api/dashboard.py` | 后台管理仪表盘 API |
| `backend/api/ai_config.py` | AI 配置管理 API |
| `backend/api/ai_records.py` | AI 问数记录 API (含前台接口) |

### 1.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `backend/main.py` | 注册新创建的路由模块 |
| `frontend/src/router/index.js` | 添加后台仪表盘、AI 问数路由 |
| `frontend/src/views/admin/Layout.vue` | 添加 AI 问数管理菜单、更新面包屑导航 |
| `frontend/src/views/portal/Layout.vue` | 添加 AI 智能问数导航菜单 |

---

## 二、后台仪表盘功能说明

### 2.1 KPI 统计卡片 (6 个)

| 卡片名称 | 数据来源 | 说明 |
|---------|---------|------|
| 数据表总数 | information_schema.tables | 统计数据库中表的总数量 |
| ETL 任务数 | etl_tasks 表 | 统计 ETL 任务的总数量 |
| 报表指标数 | reports 表 | 统计报表配置的总数量 |
| 用户总数 | users 表 | 统计系统用户的总数量 |
| 今日查询次数 | system_logs 表 | 统计今日的查询操作次数 |
| 系统运行时长 | system_logs 最早记录 | 从首次日志记录计算运行时长 |

### 2.2 图表展示

#### ETL 任务执行趋势（近 7 天）
- **类型**: 折线图 + 面积图
- **数据源**: etl_logs 表
- **功能**: 展示近 7 天每天的 ETL 任务执行次数

#### 查询热度排行（Top 10 报表）
- **类型**: 横向柱状图
- **数据源**: system_logs + reports 表关联统计
- **功能**: 展示被查询次数最多的前 10 个报表

#### 系统资源使用率
- **类型**: 进度条列表
- **数据源**: psutil 库实时获取
- **指标**: CPU 使用率、内存使用率、磁盘使用率、数据库连接数

### 2.3 快捷操作

| 操作按钮 | 功能说明 | 跳转/动作 |
|---------|---------|----------|
| 运行全部 ETL | 触发所有 ETL 任务执行 | 确认后执行 |
| 查看系统日志 | 查看系统日志列表 | 跳转 /admin/monitor/logs |
| 用户管理 | 管理系统用户 | 跳转 /admin/users |
| 报表配置 | 管理报表配置 | 跳转 /admin/reports |

### 2.4 技术特点

- 使用 ECharts 实现数据可视化
- 每 30 秒自动刷新资源使用率
- 响应式布局，支持不同屏幕尺寸
- ERP 商务风格配色方案

---

## 三、AI 问数前后台功能对比

### 3.1 前台功能 (/portal/ai-query)

| 功能模块 | 详细说明 |
|---------|---------|
| **自然语言查询** | 提供文本输入框，支持 Ctrl+Enter 快捷查询 |
| **快捷问题模板** | 预设 5 个常见问题，点击即可填充 |
| **查询历史** | 展示当前用户的查询历史记录（最多 10 条） |
| **结果展示** | SQL 代码高亮显示 + 表格展示查询结果 |
| **SQL 复制** | 一键复制生成的 SQL 语句 |
| **数据导出** | 支持将查询结果导出为 JSON 文件 |

#### 权限控制
- ✅ 仅允许 SELECT 查询
- ✅ 敏感表/字段过滤（users, roles, permissions 等）
- ✅ 查询次数限制（每日配额管理）
- ✅ 敏感词过滤（DROP, DELETE, TRUNCATE 等）

### 3.2 后台管理功能

#### AI 配置管理 (/admin/ai-query)

| 配置模块 | 功能说明 |
|---------|---------|
| **API 配置** | 配置 DASHSCOPE_API_KEY、API 地址、模型选择 |
| **Prompt 模板** | 管理系统提示词和用户提示词模板 |
| **表结构映射** | 配置数据表的中文名称、字段说明 |
| **权限配置** | 配置查询类型限制、每日配额、敏感词、敏感表 |
| **用户权限** | 管理每个用户的 AI 权限开关和配额 |

#### 问数记录 (/admin/ai-records)

| 功能模块 | 功能说明 |
|---------|---------|
| **查询记录** | 展示所有用户的 AI 查询历史记录 |
| **搜索筛选** | 支持按用户名、关键词、状态、日期范围筛选 |
| **统计卡片** | 总查询次数、成功次数、失败次数、成功率 |
| **详情查看** | 查看完整的查询详情，包括问题、SQL、结果数据 |
| **失败重试** | 对失败的查询支持重新执行 |
| **数据导出** | 导出查询记录为 JSON 文件 |

### 3.3 功能对比表

| 功能 | 前台 | 后台 |
|------|------|------|
| 自然语言查询 | ✅ | ❌ |
| 快捷问题 | ✅ | ❌ |
| 查询历史 (个人) | ✅ | ❌ |
| 结果展示 | ✅ | ❌ |
| SQL 复制/导出 | ✅ | ❌ |
| 配额查询 | ✅ | ❌ |
| AI 配置管理 | ❌ | ✅ |
| Prompt 模板管理 | ❌ | ✅ |
| 表结构映射 | ❌ | ✅ |
| 全部查询记录 | ❌ | ✅ |
| 查询统计分析 | ❌ | ✅ |
| 用户权限管理 | ❌ | ✅ |
| 敏感词配置 | ❌ | ✅ |

---

## 四、用户管理权限说明

### 4.1 权限层级

| 角色 | 角色 ID | 权限说明 |
|------|--------|---------|
| 超级管理员 | 1 | 拥有所有权限，包括系统配置、用户管理、AI 配置等 |
| 分析师 | 2 | 拥有报表查看、数据分析、AI 问数等权限 |
| 普通用户 | 3 | 仅拥有基本的报表查看权限 |

### 4.2 用户管理功能

#### 已有功能（backend/api/users.py）
- ✅ 用户列表（分页、搜索、筛选）
- ✅ 创建用户
- ✅ 编辑用户
- ✅ 删除用户
- ✅ 重置密码
- ✅ 启用/禁用用户
- ✅ 角色分配

#### AI 相关权限（backend/api/ai_config.py）
- ✅ AI 权限开关（ai_enabled 字段）
- ✅ 每日配额管理（ai_quota 字段）
- ✅ 今日已用统计（ai_used_today 字段）

### 4.3 数据库字段说明

#### users 表新增字段
```sql
-- AI 问数权限相关字段
ALTER TABLE users ADD COLUMN ai_enabled TINYINT(1) DEFAULT 1 COMMENT 'AI 问数权限：1-启用，0-禁用';
ALTER TABLE users ADD COLUMN ai_quota INT DEFAULT 100 COMMENT '每日 AI 查询配额';
ALTER TABLE users ADD COLUMN ai_used_today INT DEFAULT 0 COMMENT '今日已用查询次数';
```

#### ai_query_logs 表
```sql
CREATE TABLE ai_query_logs (
    query_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    question TEXT NOT NULL COMMENT '用户问题',
    sql TEXT COMMENT '生成的 SQL',
    status VARCHAR(20) NOT NULL COMMENT '状态：success/error',
    execution_time INT DEFAULT 0 COMMENT '执行时间 (ms)',
    result_count INT DEFAULT 0 COMMENT '结果数量',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4 权限控制流程

```
用户发起 AI 查询请求
       ↓
验证用户登录状态
       ↓
检查 ai_enabled 字段 → 禁用 → 返回 403 错误
       ↓ (启用)
检查 ai_used_today >= ai_quota → 是 → 返回 429 错误
       ↓ (否)
检查问题敏感词 → 包含 → 返回 400 错误，记录日志
       ↓ (通过)
生成 SQL 并检查 → 危险 SQL → 返回 400 错误，记录日志
       ↓ (安全)
执行 SQL 查询
       ↓
返回结果 + ai_used_today + 1
       ↓
记录查询日志到 ai_query_logs
```

---

## 五、路由配置说明

### 5.1 后台管理路由

| 路径 | 组件 | 说明 |
|------|------|------|
| `/admin/dashboard` | AdminDashboard | 后台仪表盘（新增） |
| `/admin/users` | AdminUsers | 用户管理 |
| `/admin/roles` | AdminRoles | 角色管理 |
| `/admin/reports` | AdminReports | 报表管理 |
| `/admin/etl` | AdminEtlTasks | ETL 任务管理 |
| `/admin/etl/schedules` | AdminEtlSchedules | ETL 调度配置 |
| `/admin/ai-query` | AdminAIQuery | AI 配置管理（新增） |
| `/admin/ai-records` | AdminAIRecords | AI 问数记录（新增） |
| `/admin/monitor/system` | AdminMonitor | 系统信息监控 |
| `/admin/monitor/logs` | AdminMonitor | 系统日志查看 |

### 5.2 前台路由

| 路径 | 组件 | 说明 |
|------|------|------|
| `/portal` | PortalDashboard | 前台仪表板 |
| `/portal/reports` | PortalReports | 报表列表 |
| `/portal/report/:id` | PortalReportDetail | 报表详情 |
| `/portal/ai-query` | PortalAIQuery | AI 智能问数（新增） |

---

## 六、技术栈说明

### 前端
- Vue 3 (Composition API)
- Vue Router
- Element Plus
- ECharts
- Axios

### 后端
- FastAPI
- SQLAlchemy
- Pydantic
- psutil (系统监控)
- httpx (异步 HTTP 请求)

---

## 七、后续优化建议

1. **数据库迁移**: 需要执行 SQL 脚本添加 AI 相关字段
2. **AI 服务集成**: 配置 DASHSCOPE_API_KEY 以启用 AI 问数功能
3. **权限细化**: 可根据需要添加更多细粒度的权限控制
4. **性能优化**: 大数据量查询时添加缓存机制
5. **安全加固**: 生产环境建议添加 HTTPS、JWT 过期刷新等

---

## 八、使用说明

### 启动后端
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 启动前端
```bash
cd frontend
npm install
npm run dev
```

### 访问地址
- 后台管理：http://localhost:5173/admin/dashboard
- 前台系统：http://localhost:5173/portal
- API 文档：http://localhost:8000/docs

---

**汇报完成**
