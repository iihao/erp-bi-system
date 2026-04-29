# AI数据融合平台数据库文档

**文档版本：** v1.0  
**更新时间：** 2026-03-16  
**系统版本：** AI数据融合平台 v1.0.0

---

## 📊 数据库概览

### 当前使用的数据库

| 数据库类型 | 状态 | 用途 | 连接方式 |
|-----------|------|------|---------|
| **SQLite** | ✅ 主用 | 开发/测试/生产 | 文件数据库 |
| **MySQL** | ⏸️ 备用 | 生产环境（可选） | TCP 连接 |

### 数据库选择配置

```bash
# 环境变量配置
USE_SQLITE=true              # true=使用 SQLite, false=使用 MySQL
SQLITE_DB_PATH=./db/erp_bi.db
DATABASE_URL=mysql://erp_bi_user:erp_bi_pass@localhost:3306/erp_bi
```

---

## 🔌 数据库连接方式

### 方式一：SQLite（当前使用）

**配置文件：** `backend/api/database.py`

```python
# 连接参数
DB_PATH = os.getenv("SQLITE_DB_PATH", "./db/erp_bi.db")

# 连接代码
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
```

**连接字符串：**
```
sqlite:///./db/erp_bi.db
```

**物理文件位置：**
```
/Users/huangqiang/.openclaw/workspace/erp-bi-system/backend/db/erp_bi.db
```

### 方式二：MySQL（生产环境）

**连接配置：**
```python
DB_URL = os.getenv("DATABASE_URL", "mysql+pymysql://erp_bi_user:erp_bi_pass@localhost:3306/erp_bi")
```

**连接字符串格式：**
```
mysql+pymysql://用户名:密码@主机:端口/数据库名
```

**示例：**
```bash
# 本地开发
mysql+pymysql://root:password@localhost:3306/erp_bi

# 生产环境
mysql+pymysql://erp_bi_user:SecurePass123@192.168.1.100:3306/erp_bi
```

**连接代码：**
```python
from sqlalchemy import create_engine, text

engine = create_engine(DB_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM users"))
    rows = result.fetchall()
```

---

## 📋 数据表详细结构

### 1. users - 用户表

**用途：** 存储系统用户信息

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| user_id | INTEGER | ✅ | 自增 | 用户 ID（主键） |
| username | TEXT | ✅ | - | 用户名（唯一） |
| password_hash | TEXT | ✅ | - | 密码哈希 |
| email | TEXT | ❌ | - | 邮箱 |
| real_name | TEXT | ❌ | - | 真实姓名 |
| role_id | INTEGER | ❌ | - | 角色 ID（外键） |
| status | INTEGER | ❌ | 1 | 状态 (1=正常 0=禁用) |
| created_at | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 更新时间 |
| last_login_at | TIMESTAMP | ❌ | - | 最后登录时间 |
| ai_enabled | INTEGER | ❌ | 1 | AI 问数权限 |
| ai_quota | INTEGER | ❌ | 100 | 每日 AI 查询配额 |
| ai_used_today | INTEGER | ❌ | 0 | 今日已用查询次数 |

**索引：**
- PRIMARY KEY (user_id)
- UNIQUE (username)

**示例数据：**
```sql
INSERT INTO users (username, password_hash, email, real_name, role_id) 
VALUES ('admin', '$2b$12$...', 'admin@example.com', '管理员', 1);
```

---

### 2. roles - 角色表

**用途：** 存储用户角色信息

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| role_id | INTEGER | ✅ | 自增 | 角色 ID（主键） |
| role_name | TEXT | ✅ | - | 角色名称（唯一） |
| description | TEXT | ❌ | - | 角色描述 |
| created_at | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 更新时间 |

**索引：**
- PRIMARY KEY (role_id)
- UNIQUE (role_name)

**预置角色：**
```sql
INSERT INTO roles (role_name, description) VALUES
('超级管理员', '系统最高权限'),
('数据分析师', '数据分析权限'),
('普通用户', '基础查看权限');
```

---

### 3. permissions - 权限表

**用途：** 存储系统权限定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| permission_id | INTEGER | ✅ | 自增 | 权限 ID（主键） |
| permission_code | TEXT | ✅ | - | 权限代码（唯一） |
| permission_name | TEXT | ✅ | - | 权限名称 |
| resource_type | TEXT | ❌ | - | 资源类型 |
| parent_id | INTEGER | ❌ | 0 | 父权限 ID |
| sort_order | INTEGER | ❌ | 0 | 排序顺序 |
| created_at | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 创建时间 |

**索引：**
- PRIMARY KEY (permission_id)
- UNIQUE (permission_code)

---

### 4. role_permissions - 角色权限关联表

**用途：** 角色与权限的多对多关系

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | ✅ | 自增 | 主键 |
| role_id | INTEGER | ✅ | - | 角色 ID（外键） |
| permission_id | INTEGER | ✅ | - | 权限 ID（外键） |
| created_at | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 创建时间 |

**索引：**
- PRIMARY KEY (id)
- INDEX (role_id, permission_id)

---

### 5. ai_query_logs - AI 查询日志表

**用途：** 记录 AI 智能问数查询历史

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| query_id | INTEGER | ✅ | 自增 | 查询 ID（主键） |
| user_id | INTEGER | ✅ | - | 用户 ID |
| username | TEXT | ✅ | - | 用户名 |
| question | TEXT | ✅ | - | 用户问题 |
| sql | TEXT | ❌ | - | 生成的 SQL |
| status | TEXT | ✅ | - | 状态 (success/error) |
| execution_time | INTEGER | ❌ | 0 | 执行时间 (ms) |
| result_count | INTEGER | ❌ | 0 | 结果数量 |
| error_message | TEXT | ❌ | - | 错误信息 |
| created_at | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 创建时间 |

**索引：**
- PRIMARY KEY (query_id)
- INDEX (user_id)
- INDEX (username)
- INDEX (status)
- INDEX (created_at)

**示例数据：**
```sql
INSERT INTO ai_query_logs (user_id, username, question, sql, status, execution_time)
VALUES (1, 'admin', '本月销售额是多少', 'SELECT SUM(final_amount)...', 'success', 1250);
```

---

### 6. report_configs - 报表配置表

**用途：** 存储报表配置信息

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| report_id | INTEGER | ✅ | 自增 | 报表 ID（主键） |
| report_name | TEXT | ✅ | - | 报表名称 |
| report_type | TEXT | ✅ | - | 报表类型 |
| description | TEXT | ❌ | - | 报表描述 |
| sql_query | TEXT | ❌ | - | SQL 查询语句 |
| config_json | TEXT | ❌ | - | 配置 JSON |
| status | TEXT | ❌ | 'draft' | 状态 (draft/published) |
| created_by | INTEGER | ❌ | - | 创建人 ID |
| created_at | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 更新时间 |

**索引：**
- PRIMARY KEY (report_id)
- INDEX (status)
- INDEX (created_by)

---

### 7. etl_task_logs - ETL 任务日志表

**用途：** 记录 ETL 任务执行日志

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| log_id | INTEGER | ✅ | 自增 | 日志 ID（主键） |
| task_name | TEXT | ✅ | - | 任务名称 |
| task_layer | TEXT | ❌ | - | 任务分层 (ODS/DW/DM) |
| status | TEXT | ✅ | - | 状态 (success/failed/running) |
| start_time | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 开始时间 |
| end_time | TIMESTAMP | ❌ | - | 结束时间 |
| duration_seconds | INTEGER | ❌ | - | 执行时长 (秒) |
| message | TEXT | ❌ | - | 执行消息 |
| error_message | TEXT | ❌ | - | 错误信息 |

**索引：**
- PRIMARY KEY (log_id)
- INDEX (task_name)
- INDEX (status)
- INDEX (start_time)

---

### 8. etl_schedules - ETL 调度配置表

**用途：** 存储 ETL 任务调度配置

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| schedule_id | INTEGER | ✅ | 自增 | 调度 ID（主键） |
| task_name | TEXT | ✅ | - | 任务名称 |
| cron_expression | TEXT | ❌ | - | Cron 表达式 |
| enabled | INTEGER | ❌ | 1 | 是否启用 |
| last_run_at | TIMESTAMP | ❌ | - | 最后执行时间 |
| next_run_at | TIMESTAMP | ❌ | - | 下次执行时间 |
| created_at | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 创建时间 |

**索引：**
- PRIMARY KEY (schedule_id)
- INDEX (enabled)
- INDEX (next_run_at)

---

### 9. system_logs - 系统日志表

**用途：** 记录系统操作日志

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| log_id | INTEGER | ✅ | 自增 | 日志 ID（主键） |
| log_level | TEXT | ❌ | 'INFO' | 日志级别 |
| module | TEXT | ❌ | - | 模块名称 |
| action | TEXT | ❌ | - | 操作名称 |
| user_id | INTEGER | ❌ | - | 用户 ID |
| username | TEXT | ❌ | - | 用户名 |
| ip_address | TEXT | ❌ | - | IP 地址 |
| message | TEXT | ❌ | - | 日志消息 |
| request_data | TEXT | ❌ | - | 请求数据 |
| response_data | TEXT | ❌ | - | 响应数据 |
| created_at | TIMESTAMP | ❌ | CURRENT_TIMESTAMP | 创建时间 |

**索引：**
- PRIMARY KEY (log_id)
- INDEX (log_level)
- INDEX (user_id)
- INDEX (created_at)

---

## 🔧 数据库操作示例

### 通用查询函数

```python
# 导入模块
from api.database import execute_query, execute_update

# 查询示例
users = execute_query("SELECT * FROM users WHERE status = ?", (1,))

# 更新示例
execute_update("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE user_id = ?", (1,))
```

### SQLAlchemy 直接连接

```python
from sqlalchemy import create_engine, text

# MySQL 连接
engine = create_engine("mysql+pymysql://user:pass@localhost/erp_bi")

# SQLite 连接
engine = create_engine("sqlite:///./db/erp_bi.db")

# 执行查询
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM users"))
    for row in result:
        print(row)
```

### 数据库备份

```bash
# SQLite 备份
cp ./db/erp_bi.db ./db/erp_bi.db.backup.$(date +%Y%m%d)

# MySQL 备份
mysqldump -u erp_bi_user -p erp_bi > backup_$(date +%Y%m%d).sql

# MySQL 恢复
mysql -u erp_bi_user -p erp_bi < backup_20260316.sql
```

---

## 📈 数据库统计

### 当前数据量（SQLite）

```bash
$ sqlite3 ./db/erp_bi.db "SELECT name FROM sqlite_master WHERE type='table';"
ai_query_logs
etl_schedules
etl_task_logs
permissions
report_configs
role_permissions
roles
system_logs
users
```

### 表空间使用

| 表名 | 预估行数 | 主要用途 |
|------|---------|---------|
| users | 100+ | 用户管理 |
| ai_query_logs | 1000+ | AI 查询记录 |
| system_logs | 5000+ | 系统日志 |
| report_configs | 50+ | 报表配置 |
| etl_task_logs | 500+ | ETL 日志 |

---

## 🔐 安全建议

### 1. 生产环境配置
- [ ] 使用 MySQL 替代 SQLite
- [ ] 配置数据库连接池
- [ ] 启用 SSL 加密连接
- [ ] 限制数据库用户权限

### 2. 密码安全
- [ ] 使用 bcrypt 加密密码
- [ ] 定期更换数据库密码
- [ ] 不在代码中硬编码密码

### 3. 备份策略
- [ ] 每日自动备份
- [ ] 备份文件加密存储
- [ ] 定期恢复测试

### 4. 监控告警
- [ ] 连接数监控
- [ ] 慢查询日志
- [ ] 磁盘空间告警

---

## 📞 技术支持

**数据库版本：**
- SQLite: 3.x (当前使用)
- MySQL: 8.0+ (推荐生产环境)

**相关文档：**
- [SQLite 官方文档](https://www.sqlite.org/docs.html)
- [MySQL 官方文档](https://dev.mysql.com/doc/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)

---

**文档结束**
