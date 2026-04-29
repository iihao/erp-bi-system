# AI数据融合 数据中台 ETL 功能文档

**版本：** v2.0  
**更新时间：** 2026-03-16  
**功能状态：** ✅ 已实现

---

## 📊 ETL 功能概览

### 核心功能模块

| 模块 | 状态 | API 端点 | 说明 |
|------|------|---------|------|
| 数据源管理 | ✅ | `/api/admin/etl/datasource` | MySQL/PostgreSQL/CSV/Excel/API |
| 数据抽取 | ✅ | `/api/admin/etl/manager` | 全量/增量抽取 |
| 数据转换 | ✅ | `/api/admin/etl/transform` | 字段映射/清洗/聚合 |
| 数据加载 | ✅ | `/api/admin/etl/editor` | 批量加载/事务控制 |
| 任务调度 | ✅ | `/api/admin/etl/schedule` | Cron 调度/依赖管理 |
| 质量检查 | ✅ | `/api/admin/etl/quality` | 规则定义/质量监控 |
| 执行监控 | ✅ | `/api/admin/etl/monitor` | 日志/告警/性能 |

---

## 🔌 1. 数据源管理

### 支持的数据源类型

| 类型 | 驱动 | 支持功能 |
|------|------|---------|
| **MySQL** | pymysql | 连接测试/元数据获取/数据读取 |
| **PostgreSQL** | psycopg2 | 连接测试/元数据获取/数据读取 |
| **CSV** | csv | 文件读取/列识别 |
| **Excel** | openpyxl | 文件读取/多 Sheet 支持 |
| **API** | httpx | REST API 调用/JSON 解析 |

### API 接口

#### 创建数据源
```http
POST /api/admin/etl/datasource/create
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "销售数据库",
  "type": "mysql",
  "host": "192.168.1.100",
  "port": 3306,
  "database": "sales_db",
  "username": "etl_user",
  "password": "password123",
  "description": "公司销售业务数据库"
}
```

#### 测试连接
```http
POST /api/admin/etl/datasource/test
Content-Type: application/json

{
  "type": "mysql",
  "host": "192.168.1.100",
  "port": 3306,
  "database": "sales_db",
  "username": "etl_user",
  "password": "password123"
}
```

**响应：**
```json
{
  "success": true,
  "message": "MySQL 连接成功"
}
```

#### 获取表结构
```http
GET /api/admin/etl/datasource/{source_id}/tables
Authorization: Bearer {token}
```

**响应：**
```json
{
  "tables": [
    {
      "table_name": "sales_orders",
      "columns": [
        {"name": "id", "type": "INT", "nullable": false},
        {"name": "order_no", "type": "VARCHAR(50)", "nullable": false},
        {"name": "customer_id", "type": "INT", "nullable": true},
        {"name": "order_date", "type": "DATE", "nullable": true},
        {"name": "final_amount", "type": "DECIMAL(10,2)", "nullable": true}
      ]
    }
  ]
}
```

### 数据库表结构

```sql
CREATE TABLE etl_datasources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,          -- 数据源名称
    type TEXT NOT NULL,                 -- mysql/postgresql/csv/excel/api
    host TEXT,                          -- 主机地址
    port INTEGER,                       -- 端口
    database TEXT,                      -- 数据库名
    username TEXT,                      -- 用户名
    password TEXT,                      -- 密码（加密）
    connection_string TEXT,             -- 连接字符串
    file_path TEXT,                     -- 文件路径（CSV/Excel）
    api_url TEXT,                       -- API 地址
    description TEXT,                   -- 描述
    config_json TEXT,                   -- 扩展配置
    is_enabled INTEGER DEFAULT 1,       -- 是否启用
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 🔄 2. 数据转换

### 转换规则类型

| 规则类型 | 说明 | 配置示例 |
|---------|------|---------|
| **字段映射** | 源字段→目标字段映射 | `{"target_field": "user_id", "transform_type": "none"}` |
| **数据清洗** | 去除空值/重复值/标准化 | `{"rule": "remove_null", "field": "name"}` |
| **数据聚合** | GROUP BY/聚合函数 | `{"group_by": ["category"], "aggregations": [{"field": "amount", "function": "SUM"}]}` |
| **数据连接** | JOIN 操作 | `{"join_type": "LEFT", "on": ["customer_id"]}` |
| **计算字段** | 自定义表达式计算 | `{"expression": "price * quantity", "result_field": "total"}` |

### API 接口

#### 创建转换任务
```http
POST /api/admin/etl/transform/create
Content-Type: application/json

{
  "name": "客户数据清洗",
  "source_datasource_id": 1,
  "source_table": "customers",
  "target_datasource_id": 2,
  "target_table": "dwd_customers",
  "extract_mode": "full",
  "transform_rules": [
    {
      "field": "customer_name",
      "rule_type": "mapping",
      "rule_config": {
        "target_field": "name",
        "transform_type": "trim"
      }
    },
    {
      "field": "email",
      "rule_type": "clean",
      "rule_config": {
        "rule": "normalize"
      }
    },
    {
      "field": "age",
      "rule_type": "calculate",
      "rule_config": {
        "expression": "YEAR(NOW()) - YEAR(birth_date)",
        "result_field": "age"
      }
    }
  ],
  "batch_size": 1000,
  "description": "客户数据清洗和标准化"
}
```

#### 验证转换规则
```http
POST /api/admin/etl/transform/validate
Content-Type: application/json

{
  "rules": [
    {"field": "name", "rule_type": "mapping", "rule_config": {"target_field": "customer_name"}}
  ]
}
```

**响应：**
```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

#### 预览转换结果
```http
POST /api/admin/etl/transform/preview
Content-Type: application/json

{
  "name": "测试任务",
  "source_datasource_id": 1,
  "source_table": "customers",
  "target_table": "dwd_customers",
  "transform_rules": [...]
}
```

**响应：**
```json
{
  "original_count": 100,
  "processed_count": 98,
  "preview": [
    {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
    {"id": 2, "name": "李四", "email": "lisi@example.com"}
  ],
  "transform_rules_applied": 5
}
```

#### 执行转换任务
```http
POST /api/admin/etl/transform/execute/{task_id}
Authorization: Bearer {token}
```

**响应：**
```json
{
  "message": "转换任务执行成功",
  "processed_rows": 1000,
  "log_id": 123
}
```

### 数据库表结构

```sql
CREATE TABLE etl_transform_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,          -- 任务名称
    source_datasource_id INTEGER,       -- 源数据源 ID
    source_table TEXT NOT NULL,         -- 源表名
    target_datasource_id INTEGER,       -- 目标数据源 ID
    target_table TEXT NOT NULL,         -- 目标表名
    transform_rules_json TEXT,          -- 转换规则（JSON）
    extract_mode TEXT DEFAULT 'full',   -- full/incremental
    extract_field TEXT,                 -- 增量字段
    batch_size INTEGER DEFAULT 1000,    -- 批量大小
    description TEXT,
    is_enabled INTEGER DEFAULT 1,
    last_run_at TIMESTAMP,
    last_status TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 📅 3. 任务调度

### Cron 表达式格式

```
* * * * * *
│ │ │ │ │ │
│ │ │ │ │ └─ 星期 (0-6, 0=周日)
│ │ │ │ └─── 月份 (1-12)
│ │ │ └───── 日期 (1-31)
│ │ └─────── 小时 (0-23)
│ └───────── 分钟 (0-59)
└─────────── 秒 (0-59, 可选)
```

### 调度配置示例

```json
{
  "task_name": "销售数据同步",
  "cron_expression": "0 0 2 * * *",  -- 每天凌晨 2 点
  "timezone": "Asia/Shanghai",
  "retry_times": 3,
  "retry_interval": 300,
  "timeout_seconds": 3600
}
```

### 任务依赖关系

```sql
-- 任务 B 依赖任务 A 完成
INSERT INTO etl_task_dependencies (task_id, depends_on_task_id, dependency_type)
VALUES (2, 1, 'success');  -- 任务 2 等待任务 1 成功
```

### 数据库表结构

```sql
CREATE TABLE etl_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    task_id INTEGER,                    -- 关联任务 ID
    cron_expression TEXT NOT NULL,
    timezone TEXT DEFAULT 'Asia/Shanghai',
    is_enabled INTEGER DEFAULT 1,
    retry_times INTEGER DEFAULT 0,
    retry_interval INTEGER DEFAULT 300,
    timeout_seconds INTEGER DEFAULT 3600,
    last_run_at TIMESTAMP,
    last_run_status TEXT,
    last_run_duration INTEGER,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 🔍 4. 数据质量

### 质量规则类型

| 规则类型 | 说明 | 配置示例 |
|---------|------|---------|
| **not_null** | 非空检查 | `{"field": "id", "rule_type": "not_null"}` |
| **unique** | 唯一性检查 | `{"field": "email", "rule_type": "unique"}` |
| **range** | 范围检查 | `{"field": "age", "min": 0, "max": 150}` |
| **regex** | 正则匹配 | `{"field": "phone", "pattern": "^1[3-9]\\d{9}$"}` |
| **custom** | 自定义 SQL | `{"expression": "amount > 0"}` |

### API 接口

#### 创建质量规则
```http
POST /api/admin/etl/quality/rule/create
Content-Type: application/json

{
  "task_id": 1,
  "table_name": "customers",
  "field_name": "email",
  "rule_type": "regex",
  "rule_expression": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
  "error_message": "邮箱格式不正确",
  "severity": "error"
}
```

#### 执行质量检查
```http
POST /api/admin/etl/quality/check/{rule_id}
Authorization: Bearer {token}
```

**响应：**
```json
{
  "rule_id": 1,
  "check_time": "2026-03-16 23:30:00",
  "total_rows": 1000,
  "failed_rows": 15,
  "failed_sample": [
    {"id": 123, "email": "invalid"},
    {"id": 456, "email": "test@com"}
  ],
  "pass_rate": 98.5
}
```

### 数据库表结构

```sql
CREATE TABLE etl_quality_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    table_name TEXT NOT NULL,
    field_name TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    rule_expression TEXT,
    error_message TEXT,
    severity TEXT DEFAULT 'warning',
    is_enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP
);

CREATE TABLE etl_quality_check_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL,
    task_log_id INTEGER,
    check_time TIMESTAMP,
    total_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,
    failed_sample TEXT
);
```

---

## 📊 5. 执行监控

### 任务日志

```sql
CREATE TABLE etl_task_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    task_type TEXT DEFAULT 'ETL',       -- ETL/TRANSFORM/LOAD
    task_id INTEGER,
    task_layer TEXT,                    -- ODS/DW/DM
    datasource_id INTEGER,
    status TEXT NOT NULL,               -- success/failed/running
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    source_rows INTEGER DEFAULT 0,      -- 源数据行数
    target_rows INTEGER DEFAULT 0,      -- 目标数据行数
    transformed_rows INTEGER DEFAULT 0, -- 转换后行数
    failed_rows INTEGER DEFAULT 0,      -- 失败行数
    message TEXT,
    error_message TEXT,
    metrics_json TEXT                   -- 性能指标
);
```

### 监控指标

| 指标 | 说明 | 计算方式 |
|------|------|---------|
| **成功率** | 任务执行成功比例 | success_count / total_runs |
| **平均耗时** | 平均执行时长 | SUM(duration) / COUNT(*) |
| **数据量** | 处理的数据行数 | SUM(source_rows) |
| **失败率** | 失败行数比例 | failed_rows / total_rows |

### 告警规则

```json
{
  "rule_name": "任务失败告警",
  "condition": "status = 'failed'",
  "notification": {
    "type": "email",
    "recipients": ["admin@example.com"],
    "subject": "ETL 任务失败告警：{task_name}"
  }
}
```

---

## 🎯 6. 典型使用场景

### 场景 1：每日销售数据同步

**需求：** 每天凌晨 2 点从业务库同步销售数据到数仓

**配置步骤：**

1. **创建数据源**
```bash
POST /api/admin/etl/datasource/create
{
  "name": "业务数据库",
  "type": "mysql",
  "host": "192.168.1.100",
  "database": "business_db"
}
```

2. **创建转换任务**
```bash
POST /api/admin/etl/transform/create
{
  "name": "销售数据同步",
  "source_datasource_id": 1,
  "source_table": "sales_orders",
  "target_datasource_id": 2,
  "target_table": "ods_sales_orders",
  "extract_mode": "incremental",
  "extract_field": "order_date"
}
```

3. **配置调度**
```bash
POST /api/admin/etl/schedule/create
{
  "task_name": "销售数据同步",
  "cron_expression": "0 0 2 * * *",
  "timezone": "Asia/Shanghai"
}
```

### 场景 2：客户数据清洗

**需求：** 清洗客户数据，去除重复值，标准化邮箱格式

**转换规则：**

```json
{
  "name": "客户数据清洗",
  "transform_rules": [
    {
      "field": "customer_name",
      "rule_type": "clean",
      "rule_config": {"rule": "trim"}
    },
    {
      "field": "email",
      "rule_type": "clean",
      "rule_config": {"rule": "normalize"}
    },
    {
      "field": "phone",
      "rule_type": "calculate",
      "rule_config": {
        "expression": "REPLACE(phone, '-', '')",
        "result_field": "phone_clean"
      }
    }
  ]
}
```

### 场景 3：数据质量监控

**需求：** 监控关键数据表的质量

**质量规则：**

```json
[
  {"table": "customers", "field": "id", "rule": "not_null"},
  {"table": "customers", "field": "email", "rule": "regex", "pattern": "^[\\w.-]+@[\\w.-]+\\.[a-zA-Z]{2,}$"},
  {"table": "orders", "field": "amount", "rule": "range", "min": 0}
]
```

---

## 📈 7. 性能优化建议

### 批量处理
- 推荐批量大小：1000-5000 条/批
- 大批量数据使用分页抽取

### 增量同步
- 使用时间戳或自增 ID 识别增量
- 记录上次同步的 max_id 或 max_time

### 并行处理
- 独立任务可并行执行
- 依赖任务按 DAG 顺序执行

### 资源限制
- 单个任务超时：1 小时
- 并发任务数：≤ 5
- 内存使用：≤ 2GB/任务

---

## 🔐 8. 安全建议

### 密码加密
- 数据源密码使用 AES 加密存储
- 不在日志中输出敏感信息

### 权限控制
- 基于角色的数据源访问控制
- 任务执行权限分离

### 审计日志
- 记录所有配置变更
- 记录任务执行日志

---

**文档结束**

**相关文档：**
- [数据库文档](./DATABASE_DOCUMENTATION.md)
- [代码巡检报告](./CODE_INSPECTION_REPORT.md)
