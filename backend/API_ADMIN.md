# AI数据融合平台后台管理 API 文档

## 概述

本文档描述了 AI数据融合平台后台管理核心功能的 API 接口。

## 认证

所有后台管理接口需要使用 JWT Bearer Token 认证。

请求头示例：
```
Authorization: Bearer <your_token>
```

## API 列表

### 1. 用户管理 (`/api/admin/users`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/users` | 获取用户列表（分页、搜索、筛选） |
| GET | `/api/admin/users/{user_id}` | 获取用户详情 |
| POST | `/api/admin/users` | 创建新用户 |
| PUT | `/api/admin/users/{user_id}` | 更新用户信息 |
| DELETE | `/api/admin/users/{user_id}` | 删除用户 |
| POST | `/api/admin/users/{user_id}/reset-password` | 重置用户密码 |
| POST | `/api/admin/users/{user_id}/toggle-status` | 启用/禁用用户 |
| GET | `/api/admin/users/roles/options` | 获取角色选项列表 |

**用户列表查询参数：**
- `page`: 页码 (默认 1)
- `page_size`: 每页数量 (默认 10)
- `keyword`: 搜索关键词 (用户名/邮箱/姓名)
- `role_id`: 角色 ID 筛选
- `status`: 状态筛选 (1-启用，0-禁用)

### 2. 角色管理 (`/api/admin/roles`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/roles` | 获取角色列表 |
| GET | `/api/admin/roles/{role_id}` | 获取角色详情 |
| POST | `/api/admin/roles` | 创建新角色 |
| PUT | `/api/admin/roles/{role_id}` | 更新角色信息 |
| DELETE | `/api/admin/roles/{role_id}` | 删除角色 |
| GET | `/api/admin/roles/{role_id}/permissions` | 获取角色权限 |
| PUT | `/api/admin/roles/{role_id}/permissions` | 设置角色权限 |
| GET | `/api/admin/roles/{role_id}/permissions/tree` | 获取角色权限树 |
| GET | `/api/admin/roles/{role_id}/users` | 获取角色下的用户 |

### 3. 权限管理 (`/api/admin/permissions`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/permissions` | 获取权限列表（树形结构） |
| GET | `/api/admin/menus` | 获取菜单树 |
| GET | `/api/admin/permissions/options` | 获取权限选项 |
| GET | `/api/admin/users/{user_id}/permissions` | 获取用户权限 |

### 4. 报表管理 (`/api/admin/reports`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/reports` | 获取报表列表 |
| GET | `/api/admin/reports/{report_id}` | 获取报表详情 |
| POST | `/api/admin/reports` | 创建报表配置 |
| PUT | `/api/admin/reports/{report_id}` | 更新报表配置 |
| DELETE | `/api/admin/reports/{report_id}` | 删除报表 |
| POST | `/api/admin/reports/{report_id}/publish` | 发布报表 |
| POST | `/api/admin/reports/{report_id}/unpublish` | 取消发布报表 |
| GET | `/api/admin/reports/types/options` | 获取报表类型选项 |

**报表列表查询参数：**
- `page`: 页码 (默认 1)
- `page_size`: 每页数量 (默认 10)
- `keyword`: 搜索关键词
- `report_type`: 类型筛选 (chart/table/kpi)
- `status`: 状态筛选 (draft/published/archived)

### 5. ETL 管理 (`/api/admin/etl`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/etl/tasks` | 获取 ETL 任务列表 |
| POST | `/api/admin/etl/tasks/{task_id}/run` | 运行 ETL 任务 |
| GET | `/api/admin/etl/tasks/{task_id}/log` | 查看任务日志 |
| GET | `/api/admin/etl/schedules` | 获取调度配置列表 |
| POST | `/api/admin/etl/schedules` | 创建调度配置 |
| PUT | `/api/admin/etl/schedules/{schedule_id}` | 更新调度配置 |
| DELETE | `/api/admin/etl/schedules/{schedule_id}` | 删除调度配置 |
| GET | `/api/admin/etl/layers/options` | 获取数仓分层选项 |

**ETL 任务列表查询参数：**
- `layer`: 数仓分层筛选 (ODS/DWD/DWS/ADS)

**任务日志查询参数：**
- `page`: 页码 (默认 1)
- `page_size`: 每页数量 (默认 20)

### 6. 运维监控 (`/api/admin/monitor`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/monitor/system` | 获取系统信息 |
| GET | `/api/admin/monitor/metrics` | 获取性能指标 |
| GET | `/api/admin/monitor/services` | 获取服务状态 |
| GET | `/api/admin/monitor/logs` | 获取系统日志 |
| POST | `/api/admin/monitor/logs` | 创建系统日志 |
| GET | `/api/admin/monitor/metrics/history` | 获取指标历史 |
| GET | `/api/admin/monitor/health` | 健康检查 |

**系统日志查询参数：**
- `page`: 页码 (默认 1)
- `page_size`: 每页数量 (默认 20)
- `level`: 日志级别 (DEBUG/INFO/WARNING/ERROR)
- `module`: 模块筛选
- `keyword`: 搜索关键词

## 响应格式

### 成功响应

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 10
}
```

### 错误响应

```json
{
  "detail": "错误消息"
}
```

## 数据库表结构

详见 `backend/db/init.sql`

主要表：
- `users` - 用户表
- `roles` - 角色表
- `permissions` - 权限表
- `role_permissions` - 角色权限关联表
- `report_configs` - 报表配置表
- `etl_task_logs` - ETL 任务日志表
- `etl_schedules` - ETL 调度配置表
- `system_logs` - 系统日志表

## 默认账号

- 用户名：`admin`
- 密码：`admin123`
