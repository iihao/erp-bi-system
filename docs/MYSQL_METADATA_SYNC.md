# MySQL 数据源连接 + 元数据同步实施报告

**实施时间：** 2026-03-18 15:30  
**实施人员：** mac🦀  
**功能模块：** 数据源管理 - MySQL 连接与元数据同步

---

## 📋 一、实施概述

本次实施完成了 MySQL 数据源的连接功能和元数据自动同步到数仓 ODS 层的功能：

1. ✅ **MySQL 连接** - 支持 MySQL 8.0/MariaDB 数据库连接
2. ✅ **元数据采集** - 自动获取 MySQL 表结构和数据
3. ✅ **ODS 层同步** - 创建 ODS 表并同步数据
4. ✅ **类型映射** - MySQL 到 SQLite 类型自动转换
5. ✅ **前端界面** - 添加同步按钮和状态显示

---

## 🔧 二、核心功能

### 2.1 MySQL 连接函数

**文件：** `backend/api/datasources.py`

```python
def get_database_connection(db_type, host, port, database, username, password):
    """根据数据库类型获取连接"""
    if db_type.lower() in ['mysql', 'mysql8', 'mariadb']:
        import pymysql
        return pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
```

**依赖：**
```bash
pip install pymysql
```

### 2.2 元数据同步函数

**功能：**
- 获取 MySQL 所有表
- 创建对应的 ODS 表（SQLite）
- 同步表数据（全量，限制 10000 条）
- 添加数仓标准字段（dt, created_at）

```python
def sync_mysql_metadata(datasource_id, db_type, host, port, database, username, password):
    """同步 MySQL 元数据到数仓 ODS 层"""
    # 1. 连接 MySQL 数据源
    mysql_conn = get_database_connection(db_type, host, port, database, username, password)
    
    # 2. 连接本地 SQLite 数仓
    with get_db_connection() as warehouse_conn:
        # 3. 获取 MySQL 所有表
        mysql_cursor.execute("SHOW TABLES")
        tables = [row[f"Tables_in_{database}"] for row in mysql_cursor.fetchall()]
        
        # 4. 为每个表创建 ODS 表并同步数据
        for table in tables:
            # 获取表结构
            mysql_cursor.execute(f"DESCRIBE `{table}`")
            columns = mysql_cursor.fetchall()
            
            # 创建 ODS 表
            ods_table_name = f"ods_{table}"
            create_sql = f"CREATE TABLE IF NOT EXISTS {ods_table_name} (...)"
            warehouse_cursor.execute(create_sql)
            
            # 同步数据
            mysql_cursor.execute(f"SELECT * FROM `{table}` LIMIT 10000")
            rows = mysql_cursor.fetchall()
            
            # 批量插入到 ODS 表
            warehouse_cursor.executemany(insert_sql, batch_data)
```

### 2.3 类型映射

**MySQL → SQLite 类型映射：**

| MySQL 类型 | SQLite 类型 | 说明 |
|-----------|-----------|------|
| INT, INTEGER | INTEGER | 整数类型 |
| DECIMAL, NUMERIC | DECIMAL(15,2) | 精确小数 |
| FLOAT, DOUBLE | DECIMAL(15,2) | 浮点数 |
| DATETIME, TIMESTAMP | DATETIME | 日期时间 |
| DATE | DATE | 日期 |
| TEXT, VARCHAR, CHAR | TEXT | 文本 |

```python
def map_mysql_to_sqlite_type(mysql_type: str) -> str:
    """MySQL 类型映射到 SQLite 类型"""
    mysql_type = mysql_type.lower()
    
    if 'int' in mysql_type:
        return 'INTEGER'
    elif 'decimal' in mysql_type or 'numeric' in mysql_type:
        return 'DECIMAL(15,2)'
    elif 'datetime' in mysql_type or 'timestamp' in mysql_type:
        return 'DATETIME'
    elif 'date' in mysql_type:
        return 'DATE'
    elif 'text' in mysql_type or 'char' in mysql_type:
        return 'TEXT'
    else:
        return 'TEXT'
```

---

## 🌐 三、API 接口

### 3.1 同步元数据

**接口：** `POST /api/admin/datasources/{datasource_id}/sync-metadata`

**请求：**
```http
POST /api/admin/datasources/2/sync-metadata
Authorization: Bearer {token}
```

**响应：**
```json
{
  "success": true,
  "message": "元数据同步完成：15/15 表",
  "tables_synced": 15,
  "total_tables": 15
}
```

**错误响应：**
```json
{
  "detail": "同步失败：无法连接 MySQL 服务器"
}
```

---

## 🎨 四、前端界面

### 4.1 数据源列表

**新增操作按钮：**
- 👁️ 预览 - 查看元数据和 SQL 查询
- 🔄 同步 - 同步元数据到数仓
- 🔌 测试连接 - 测试数据库连接
- ✏️ 编辑 - 编辑数据源配置
- ⚡ 启用/禁用 - 切换数据源状态
- 🗑️ 删除 - 删除数据源

### 4.2 同步按钮

```vue
<el-button size="small" type="success" @click="syncMetadata(row)" :loading="row.syncing">
  🔄 同步
</el-button>
```

**状态显示：**
- 默认状态：🔄 同步
- 同步中：🔄 同步中...（禁用按钮）
- 同步完成：显示成功提示

### 4.3 同步确认对话框

```javascript
ElMessageBox.confirm(
  `确定要同步数据源"${row.name}"的元数据吗？这可能需要几分钟时间。`,
  '确认同步',
  {
    type: 'warning',
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }
)
```

---

## 📁 五、数据流

### 5.1 同步流程

```
┌─────────────────┐
│  MySQL 数据源    │
│  (业务数据库)   │
└────────┬────────┘
         │
         │ 1. SHOW TABLES
         ▼
┌─────────────────┐
│  获取表列表      │
│  (15 个表)       │
└────────┬────────┘
         │
         │ 2. DESCRIBE {table}
         ▼
┌─────────────────┐
│  获取表结构      │
│  (字段/类型)    │
└────────┬────────┘
         │
         │ 3. CREATE TABLE IF NOT EXISTS
         ▼
┌─────────────────┐
│  创建 ODS 表     │
│  (ods_{table})  │
└────────┬────────┘
         │
         │ 4. SELECT * LIMIT 10000
         ▼
┌─────────────────┐
│  读取数据        │
│  (最多 10000 条)  │
└────────┬────────┘
         │
         │ 5. INSERT OR REPLACE
         ▼
┌─────────────────┐
│  写入 ODS 层     │
│  (SQLite 数仓)   │
└─────────────────┘
```

### 5.2 ODS 表结构

**原始 MySQL 表：**
```sql
CREATE TABLE users (
  user_id INT PRIMARY KEY,
  username VARCHAR(50),
  email VARCHAR(100),
  created_at DATETIME
);
```

**同步后的 ODS 表：**
```sql
CREATE TABLE ods_users (
  `user_id` INTEGER PRIMARY KEY,
  `username` TEXT,
  `email` TEXT,
  `created_at` DATETIME,
  `dt` DATE COMMENT '数据分区日期',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔧 六、使用步骤

### 6.1 添加 MySQL 数据源

1. 访问数据源管理：`/admin/datasources`
2. 点击"➕ 新增数据源"
3. 填写配置：
   - 数据源名称：例如 `MySQL-业务库`
   - 数据库类型：选择 `mysql`
   - 主机：例如 `192.168.1.100`
   - 端口：`3306`
   - 数据库名：例如 `business_db`
   - 用户名：`root`
   - 密码：`password`
4. 点击"测试连接"验证
5. 保存数据源

### 6.2 同步元数据

1. 在数据源列表中找到刚添加的 MySQL 数据源
2. 点击"🔄 同步"按钮
3. 确认同步对话框
4. 等待同步完成（显示进度）
5. 查看同步结果

### 6.3 验证同步结果

**方法 1：查看 ODS 表**
```sql
SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ods_%';
```

**方法 2：前端预览**
1. 点击"👁️ 预览"按钮
2. 查看表列表（应包含 ods_开头的表）
3. 点击表名查看结构

**方法 3：SQL 查询**
```sql
SELECT * FROM ods_users LIMIT 10;
```

---

## 📊 七、同步策略

### 7.1 全量同步

**当前实现：**
- 每次同步读取最多 10000 条数据
- 使用 `INSERT OR REPLACE` 避免重复
- 添加 `dt` 字段标记同步日期

**适用场景：**
- 小数据量表（< 10000 条）
- 初次同步
- 数据变更频繁的表

### 7.2 增量同步（待实现）

**实现思路：**
```sql
-- 记录上次同步时间
SELECT MAX(created_at) as last_sync FROM ods_users;

-- 只同步新增数据
SELECT * FROM users 
WHERE created_at > :last_sync;
```

**优势：**
- 减少数据传输量
- 提高同步速度
- 降低数据库负载

---

## 🔐 八、安全考虑

### 8.1 密码保护

**现状：**
- ⚠️ 密码明文存储在 SQLite 中
- ⚠️ API 响应包含密码字段

**改进建议：**
```python
from cryptography.fernet import Fernet

# 加密存储
cipher = Fernet(secret_key)
encrypted_password = cipher.encrypt(password.encode())

# 解密使用
decrypted_password = cipher.decrypt(encrypted_password).decode()
```

### 8.2 连接限制

**当前限制：**
- 查询限制 10000 条
- 超时时间 30 秒
- 只读权限（建议）

**建议配置：**
```sql
-- 创建只读用户
CREATE USER 'erp_bi_reader'@'%' IDENTIFIED BY 'password';
GRANT SELECT ON business_db.* TO 'erp_bi_reader'@'%';
```

---

## 📁 九、文件清单

### 后端文件
- `backend/api/datasources.py` - ✅ 数据源 API（新增同步功能）
- `backend/api/database.py` - 数据库连接模块
- `.env` - 环境变量配置

### 前端文件
- `frontend/src/views/admin/Datasources.vue` - ✅ 数据源管理（新增同步按钮）
- `frontend/src/views/admin/DatasourcePreview.vue` - 数据源预览

### 文档文件
- `docs/MYSQL_METADATA_SYNC.md` - 本文档

---

## 🧪 十、测试验证

### 10.1 测试环境

**MySQL 测试库：**
```sql
-- 创建测试数据库
CREATE DATABASE test_bi;

-- 创建测试表
CREATE TABLE test_users (
  id INT PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(50),
  email VARCHAR(100),
  created_at DATETIME
);

-- 插入测试数据
INSERT INTO test_users (name, email) VALUES
  ('张三', 'zhangsan@example.com'),
  ('李四', 'lisi@example.com'),
  ('王五', 'wangwu@example.com');
```

### 10.2 测试步骤

1. **添加测试数据源**
   ```
   名称：MySQL-测试库
   类型：mysql
   主机：localhost
   端口：3306
   数据库：test_bi
   用户：root
   密码：password
   ```

2. **测试连接**
   - 点击"测试连接"
   - 验证连接成功

3. **同步元数据**
   - 点击"🔄 同步"
   - 确认同步
   - 等待完成

4. **验证结果**
   ```sql
   -- 检查 ODS 表
   SELECT * FROM ods_test_users;
   
   -- 验证数据
   SELECT COUNT(*) FROM ods_test_users;
   -- 应该返回 3
   ```

---

## 🚀 十一、性能优化

### 11.1 批量插入

**当前实现：**
```python
# 批量插入（1000 条/批）
batch_size = 1000
for i in range(0, len(rows), batch_size):
    batch = rows[i:i+batch_size]
    warehouse_cursor.executemany(insert_sql, batch)
```

### 11.2 并发同步

**待实现：**
```python
import asyncio
import aiofiles

# 并发同步多个表
tasks = [sync_table(table) for table in tables]
await asyncio.gather(*tasks)
```

### 11.3 索引优化

**建议添加：**
```sql
-- 为常用查询字段添加索引
CREATE INDEX idx_ods_users_created_at ON ods_users(created_at);
CREATE INDEX idx_ods_orders_order_date ON ods_orders(order_date);
```

---

## 🎓 十二、总结

本次实施完成了 MySQL 数据源的连接和元数据同步功能：

**核心价值：**
- 🔗 **MySQL 连接** - 支持业务数据库接入
- 🔄 **自动同步** - 一键同步元数据到数仓
- 📊 **ODS 层构建** - 自动创建 ODS 表结构
- 🎯 **类型映射** - 智能转换数据库类型

**技术亮点：**
- pymysql 连接管理
- 动态类型映射
- 批量数据插入
- 事务处理

**下一步：**
1. 支持 PostgreSQL 同步
2. 实现增量同步
3. 添加同步任务调度
4. 实现密码加密存储

---

**实施完成时间：** 2026-03-18 15:35  
**实施状态：** ✅ 核心功能已完成
