# AI数据融合平台 API 接口文档

## 目录

1. [后台管理仪表盘 API](#1-后台管理仪表盘-api)
2. [用户管理 API](#2-用户管理-api)
3. [AI 配置管理 API](#3-ai-配置管理-api)
4. [AI 问数记录 API](#4-ai-问数记录-api)
5. [前台 AI 问数 API](#5-前台-ai-问数-api)

---

## 1. 后台管理仪表盘 API

### 1.1 获取仪表盘 KPI 统计数据

**接口**: `GET /api/admin/dashboard/stats`

**认证**: 需要 Bearer Token

**响应示例**:
```json
{
  "table_count": 24,
  "etl_task_count": 12,
  "report_metric_count": 56,
  "user_count": 128,
  "today_query_count": 1024,
  "uptime_days": "15 天 8 小时"
}
```

### 1.2 获取 ETL 任务执行趋势

**接口**: `GET /api/admin/dashboard/etl-trend`

**认证**: 需要 Bearer Token

**响应示例**:
```json
{
  "dates": ["7 天前", "6 天前", "5 天前", "4 天前", "3 天前", "2 天前", "今天"],
  "counts": [28, 32, 25, 38, 42, 35, 45]
}
```

### 1.3 获取查询热度排行

**接口**: `GET /api/admin/dashboard/heatmap`

**认证**: 需要 Bearer Token

**响应示例**:
```json
{
  "reports": [
    {"name": "销售日报", "count": 520},
    {"name": "库存周报", "count": 450},
    {"name": "客户分析", "count": 380}
  ]
}
```

### 1.4 获取系统资源使用率

**接口**: `GET /api/admin/dashboard/resources`

**认证**: 需要 Bearer Token

**响应示例**:
```json
{
  "cpu_usage": 45.2,
  "memory_usage": 62.8,
  "disk_usage": 55.0,
  "db_connections": 28
}
```

---

## 2. 用户管理 API

### 2.1 获取用户列表

**接口**: `GET /api/admin/users`

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 10 |
| keyword | string | 否 | 搜索关键词 |
| role_id | int | 否 | 角色 ID 筛选 |
| status | int | 否 | 状态筛选 (0-禁用，1-启用) |

**响应示例**:
```json
{
  "items": [
    {
      "user_id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "real_name": "管理员",
      "role_id": 1,
      "role_name": "超级管理员",
      "status": 1,
      "created_at": "2024-01-01 00:00:00",
      "updated_at": "2024-01-15 10:30:00",
      "last_login_at": "2024-01-15 10:30:00"
    }
  ],
  "total": 128,
  "page": 1,
  "page_size": 10
}
```

### 2.2 创建用户

**接口**: `POST /api/admin/users`

**请求体**:
```json
{
  "username": "newuser",
  "password": "password123",
  "email": "user@example.com",
  "real_name": "新用户",
  "role_id": 3
}
```

### 2.3 更新用户

**接口**: `PUT /api/admin/users/{user_id}`

**请求体**:
```json
{
  "email": "updated@example.com",
  "real_name": "更新后的姓名",
  "role_id": 2
}
```

### 2.4 删除用户

**接口**: `DELETE /api/admin/users/{user_id}`

### 2.5 重置密码

**接口**: `POST /api/admin/users/{user_id}/reset-password`

**请求体**:
```json
{
  "new_password": "newpassword123"
}
```

### 2.6 启用/禁用用户

**接口**: `POST /api/admin/users/{user_id}/toggle-status`

**请求体**:
```json
{
  "status": 0
}
```

---

## 3. AI 配置管理 API

### 3.1 获取当前 AI 配置

**接口**: `GET /api/admin/ai-config/current`

**认证**: 需要 Bearer Token

**响应示例**:
```json
{
  "api_key": "sk-xxxx****",
  "base_url": "https://dashscope.aliyuncs.com/api/v1",
  "model": "qwen-plus",
  "system_prompt": "你是一个专业的 SQL 生成助手...",
  "user_prompt": "请将以下问题转换为 SQL 查询：{question}",
  "daily_quota": 100,
  "sensitive_words": "DROP, DELETE, TRUNCATE",
  "sensitive_tables": ["users", "roles"],
  "table_schemas": [...]
}
```

### 3.2 保存 API 配置

**接口**: `POST /api/admin/ai-config/api`

**请求体**:
```json
{
  "api_key": "sk-xxxxx",
  "base_url": "https://dashscope.aliyuncs.com/api/v1",
  "model": "qwen-plus"
}
```

### 3.3 保存 Prompt 模板

**接口**: `POST /api/admin/ai-config/prompt`

**请求体**:
```json
{
  "system_prompt": "你是一个专业的 SQL 生成助手...",
  "user_prompt": "请将以下问题转换为 SQL 查询：{question}"
}
```

### 3.4 保存权限配置

**接口**: `POST /api/admin/ai-config/permission`

**请求体**:
```json
{
  "allowed_types": ["SELECT"],
  "daily_quota": 100,
  "sensitive_words": "DROP, DELETE, TRUNCATE, GRANT",
  "sensitive_tables": ["users", "roles", "permissions"]
}
```

### 3.5 测试 API 连接

**接口**: `GET /api/admin/ai-config/test`

**响应示例**:
```json
{
  "status": "success",
  "message": "API 连接正常"
}
```

### 3.6 获取用户 AI 权限列表

**接口**: `GET /api/admin/ai-config/users`

**响应示例**:
```json
[
  {
    "user_id": 1,
    "username": "admin",
    "role": "管理员",
    "ai_enabled": true,
    "quota": 100,
    "used_today": 15
  }
]
```

### 3.7 切换用户 AI 权限

**接口**: `POST /api/admin/ai-config/user/{user_id}/toggle`

### 3.8 更新用户配额

**接口**: `POST /api/admin/ai-config/user/{user_id}/quota`

**参数**: `quota` (查询参数)

---

## 4. AI 问数记录 API

### 4.1 获取查询记录

**接口**: `GET /api/admin/ai-query/records`

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| username | string | 否 | 用户名筛选 |
| keyword | string | 否 | 问题/SQL 关键词 |
| status | string | 否 | 状态 (success/error) |
| start_date | string | 否 | 开始日期 (YYYY-MM-DD) |
| end_date | string | 否 | 结束日期 (YYYY-MM-DD) |

**响应示例**:
```json
{
  "items": [
    {
      "query_id": 1,
      "username": "admin",
      "question": "上个月销售额最高的产品是什么？",
      "sql": "SELECT p.product_name, SUM(soi.subtotal)...",
      "status": "success",
      "execution_time": 156,
      "result_count": 1,
      "created_at": "2024-01-15 10:30:25"
    }
  ],
  "total": 1256,
  "page": 1,
  "page_size": 20
}
```

### 4.2 获取查询统计

**接口**: `GET /api/admin/ai-query/stats`

**响应示例**:
```json
{
  "total": 1256,
  "success": 1180,
  "failed": 76,
  "rate": 94.0
}
```

### 4.3 获取查询趋势

**接口**: `GET /api/admin/ai-query/trend`

**参数**: `days` (查询天数，默认 7)

**响应示例**:
```json
{
  "days": 7,
  "data": [
    {"date": "2024-01-09", "count": 150, "success_count": 142},
    {"date": "2024-01-10", "count": 180, "success_count": 175}
  ]
}
```

---

## 5. 前台 AI 问数 API

### 5.1 执行 AI 查询

**接口**: `POST /api/portal/ai-query/execute`

**认证**: 需要 Bearer Token (portal_token)

**请求体**:
```json
{
  "question": "上个月销售额最高的产品是什么？",
  "top_k": 10
}
```

**响应示例**:
```json
{
  "sql": "SELECT p.product_name, SUM(soi.subtotal) as total...",
  "explanation": "查询产品销售排名",
  "data": [
    {"product_name": "产品 A", "total": 125000}
  ],
  "columns": ["product_name", "total"]
}
```

### 5.2 获取用户配额

**接口**: `GET /api/portal/ai-query/quota`

**认证**: 需要 Bearer Token

**响应示例**:
```json
{
  "daily": 100,
  "used": 15,
  "remaining": 85
}
```

### 5.3 获取查询历史

**接口**: `GET /api/portal/ai-query/history`

**参数**: `limit` (默认 10)

**响应示例**:
```json
{
  "history": [
    {
      "question": "上个月销售额最高的产品是什么？",
      "sql": "SELECT p.product_name...",
      "status": "success",
      "time": "2024-01-15 10:30"
    }
  ]
}
```

---

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权或 token 已过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 (配额用尽) |
| 500 | 服务器内部错误 |

## 认证方式

所有需要认证的接口需要在请求头中携带 Bearer Token:

```
Authorization: Bearer <your_token_here>
```

后台管理接口使用登录后获取的 token，前台接口使用 portal_token。
