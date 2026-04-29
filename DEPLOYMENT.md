# 快速部署指南

## 方案一：使用 Docker（推荐）

### 1. 启动 Docker

```bash
# Mac 上启动 Docker Desktop
open -a Docker
```

### 2. 启动 MySQL 数仓

```bash
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system

# 设置环境变量
export MYSQL_ROOT_PASSWORD=root123
export MYSQL_PASSWORD=erp_bi123

# 启动容器
docker-compose -f docker-compose-warehouse.yml up -d

# 查看状态
docker ps | grep erp_bi_warehouse
```

### 3. 验证

```bash
# 连接 MySQL
docker exec -it erp_bi_warehouse mysql -uerp_bi -perp_bi123 erp_bi_warehouse

# 查看表
SHOW TABLES;

# 验证表数量
SELECT 'ODS 层' AS layer, COUNT(*) AS count FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name LIKE 'ods_%'
UNION ALL SELECT 'DWD 层', COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name LIKE 'dwd_%'
UNION ALL SELECT 'DWS 层', COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name LIKE 'dws_%'
UNION ALL SELECT 'ADS 层', COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name LIKE 'ads_%'
UNION ALL SELECT '维度表', COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name LIKE 'dim_%';
```

---

## 方案二：手动安装 MySQL

### 1. 安装 MySQL 8.0

```bash
# 使用 Homebrew 安装
brew install mysql@8.0

# 启动 MySQL
brew services start mysql@8.0
```

### 2. 创建数据库

```bash
# 连接 MySQL
mysql -uroot

# 创建数据库和用户
CREATE DATABASE erp_bi_warehouse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'erp_bi'@'localhost' IDENTIFIED BY 'erp_bi123';
GRANT ALL PRIVILEGES ON erp_bi_warehouse.* TO 'erp_bi'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. 导入表结构

```bash
# 导入 DDL
mysql -uerp_bi -perp_bi123 erp_bi_warehouse < backend/db/init_warehouse_mysql.sql

# 验证
mysql -uerp_bi -perp_bi123 erp_bi_warehouse -e "SHOW TABLES;"
```

---

## 方案三：使用现有 MySQL

如果你已有 MySQL 服务器：

### 1. 修改配置

编辑 `.env` 文件：

```bash
MYSQL_HOST=你的 MySQL 主机 IP
MYSQL_PORT=3306  # 或你的端口
MYSQL_USER=erp_bi
MYSQL_PASSWORD=你的密码
MYSQL_DATABASE=erp_bi_warehouse
```

### 2. 创建数据库

```sql
CREATE DATABASE erp_bi_warehouse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 导入表结构

```bash
mysql -h 你的主机 -uerp_bi -p erp_bi_warehouse < backend/db/init_warehouse_mysql.sql
```

---

## 安装 Python 依赖

```bash
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system/backend

# 安装 MySQL 连接器
pip3 install mysql-connector-python

# 或进入虚拟环境后安装
source venv/bin/activate
pip install mysql-connector-python
```

---

## 执行 ETL

```bash
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system/backend

# 设置环境变量
export MYSQL_HOST=localhost
export MYSQL_PORT=3307  # Docker 用 3307，手动安装用 3306
export MYSQL_USER=erp_bi
export MYSQL_PASSWORD=erp_bi123
export MYSQL_DATABASE=erp_bi_warehouse

# 执行 ETL
python3 etl_pipeline.py

# 查看日志
tail -f logs/etl.log
```

---

## 常见问题

### Q1: Docker 无法启动
**解决：** 确保 Docker Desktop 已安装并运行
```bash
open -a Docker
# 等待 Docker 图标变为绿色
```

### Q2: MySQL 连接失败
**解决：** 检查端口和密码
```bash
# Docker 版本用 3307 端口
mysql -h localhost -P 3307 -uerp_bi -perp_bi123

# 手动安装用 3306 端口
mysql -h localhost -P 3306 -uerp_bi -perp_bi123
```

### Q3: 字符集错误
**解决：** 确保使用 utf8mb4
```sql
SHOW VARIABLES LIKE 'character_set%';
-- 应该显示 utf8mb4
```

### Q4: ETL 脚本找不到模块
**解决：** 安装依赖
```bash
pip3 install mysql-connector-python
```

---

## 下一步

1. ✅ 数据库表已创建（30 张）
2. ⏳ 启动 MySQL 容器
3. ⏳ 执行 ETL 流程
4. ⏳ 验证数据
5. ⏳ 开发报表

**详细文档：** `backend/db/WAREHOUSE_MYSQL_ETL.md`
