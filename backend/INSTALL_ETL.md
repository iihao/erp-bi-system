# AI数据融合 ETL 系统安装与部署指南

## 📋 一、文件清单

### 已创建/修改的文件

#### ETL 核心模块
1. `backend/etl/__init__.py` - ETL 模块初始化
2. `backend/etl/config.py` - ETL 配置管理（新增）
3. `backend/etl/utils.py` - ETL 工具函数（新增）
4. `backend/etl/extractors/__init__.py` - 抽取器初始化
5. `backend/etl/extractors/ods_extractor.py` - ODS 层数据抽取（新增）
6. `backend/etl/transformers/__init__.py` - 转换器初始化
7. `backend/etl/transformers/dwd_cleaner.py` - DWD 层数据清洗（新增）
8. `backend/etl/transformers/dws_aggregator.py` - DWS 层数据聚合（新增）
9. `backend/etl/loaders/__init__.py` - 加载器初始化
10. `backend/etl/loaders/ads_loader.py` - ADS 层报表生成（新增）

#### 调度系统模块
11. `backend/scheduler/__init__.py` - 调度器初始化
12. `backend/scheduler/config.py` - 调度器配置（新增）
13. `backend/scheduler/jobs.py` - 调度任务定义（新增）
14. `backend/scheduler/scheduler.py` - 调度器主程序（新增）

#### 脚本和文档
15. `backend/run_etl.py` - ETL 主流程脚本（新增）
16. `backend/test_etl_modules.py` - ETL 模块测试（新增）
17. `backend/ETL_SCHEDULER_MANUAL.md` - 使用手册（新增）
18. `backend/requirements.txt` - 依赖配置（已更新）

---

## 🔧 二、安装步骤

### 2.1 安装 Python 依赖

```bash
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system/backend

# 激活虚拟环境（如果有）
source venv/bin/activate

# 安装新依赖
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install apscheduler>=3.10.4
pip install mysql-connector-python>=8.2.0
```

### 2.2 配置环境变量

创建或编辑 `.env` 文件：

```bash
# MySQL 数仓配置
MYSQL_HOST=localhost
MYSQL_PORT=3307
MYSQL_USER=erp_bi
MYSQL_PASSWORD=erp_bi123
MYSQL_DATABASE=erp_bi_warehouse

# SQLite 业务库
SQLITE_DB_PATH=db/erp_bi.db

# ETL 配置
ETL_MODE=incremental
ETL_MAX_RETRIES=3
ETL_BATCH_SIZE=1000
ETL_LOG_LEVEL=INFO
ETL_LOG_DIR=logs/etl

# 调度器配置
SCHEDULER_TIMEZONE=Asia/Shanghai
SCHEDULER_THREADS=10
```

### 2.3 初始化数据库

确保 MySQL 数仓表已创建：

```bash
# 连接到 MySQL
mysql -h localhost -P 3307 -u erp_bi -p erp_bi_warehouse

# 执行建表脚本
source /Users/huangqiang/.openclaw/workspace/erp-bi-system/backend/db/init_warehouse_mysql.sql
```

验证表创建：

```sql
SELECT 'ODS 层' AS layer, COUNT(*) AS table_count FROM information_schema.tables 
WHERE table_schema = 'erp_bi_warehouse' AND table_name LIKE 'ods_%'
UNION ALL
SELECT 'DWD 层', COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'erp_bi_warehouse' AND table_name LIKE 'dwd_%'
UNION ALL
SELECT 'DWS 层', COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'erp_bi_warehouse' AND table_name LIKE 'dws_%'
UNION ALL
SELECT 'ADS 层', COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'erp_bi_warehouse' AND table_name LIKE 'ads_%';
```

期望结果：
- ODS 层：9 张表
- DWD 层：7 张表
- DWS 层：5 张表
- ADS 层：7 张表

---

## 🚀 三、快速开始

### 3.1 手动执行 ETL

```bash
# 执行完整 ETL 流程
python3 run_etl.py

# 增量模式
python3 run_etl.py --mode incremental

# 全量模式
python3 run_etl.py --mode full

# 只执行 ODS 层
python3 run_etl.py --layer ODS

# 只执行 DWD 层
python3 run_etl.py --layer DWD
```

### 3.2 启动调度器

```bash
# 启动调度器（前台运行）
python3 scheduler/scheduler.py start

# 后台运行（使用 nohup）
nohup python3 scheduler/scheduler.py start > logs/scheduler.log 2>&1 &

# 查看状态
python3 scheduler/scheduler.py status

# 停止调度器
python3 scheduler/scheduler.py stop
```

### 3.3 使用 API 管理

启动 API 服务：

```bash
python3 main_new.py
```

访问 API 文档：http://localhost:8000/docs

ETL 管理接口：
- `GET /api/admin/etl/tasks` - 获取任务列表
- `POST /api/admin/etl/tasks/{task_id}/run` - 手动触发任务
- `GET /api/admin/etl/tasks/{task_id}/log` - 查看执行日志
- `GET /api/admin/etl/schedules` - 获取调度配置
- `POST /api/admin/etl/schedules` - 创建调度配置

---

## 📊 四、验证测试

### 4.1 运行模块测试

```bash
python3 test_etl_modules.py
```

### 4.2 验证数据流转

```sql
-- 检查 ODS 层数据
SELECT COUNT(*) FROM ods_room WHERE dt = CURDATE() - INTERVAL 1 DAY;

-- 检查 DWD 层数据
SELECT COUNT(*) FROM dwd_room_detail WHERE dt = CURDATE() - INTERVAL 1 DAY;

-- 检查 DWS 层数据
SELECT COUNT(*) FROM dws_sales_payment_fact WHERE dt = CURDATE() - INTERVAL 1 DAY;

-- 检查 ADS 层数据
SELECT COUNT(*) FROM ads_sales_dashboard WHERE dt = CURDATE();
```

### 4.3 检查执行日志

```bash
# 查看最新日志
tail -f logs/etl/etl_$(date +%Y-%m-%d).log

# 查看调度器日志
tail -f logs/scheduler.log
```

---

## ⚙️ 五、配置说明

### 5.1 ETL 模式

- **incremental（增量）**: 仅处理 T+1 数据（默认）
- **full（全量）**: 清空目标表后重新加载

### 5.2 调度计划

默认调度配置（Asia/Shanghai 时区）：

| 任务 | Cron 表达式 | 说明 | 频率 |
|------|-----------|------|------|
| 完整 ETL | `0 1 * * mon` | 完整流程 | 每周一 01:00 |
| ODS 抽取 | `0 2 * * *` | ODS 层 | 每天 02:00 |
| DWD 清洗 | `0 3 * * *` | DWD 层 | 每天 03:00 |
| DWS 聚合 | `0 4 * * *` | DWS 层 | 每天 04:00 |
| ADS 报表 | `0 5 * * *` | ADS 层 | 每天 05:00 |
| 维度刷新 | `0 3 * * sun` | 维度表 | 每周日 03:00 |

### 5.3 自定义 Cron 表达式

Cron 表达式格式（5 位）：
```
分钟 小时 日期 月份 星期
 0    2    *    *    *    → 每天凌晨 2 点
 0    0    1    *    *    → 每月 1 日零点
 0    9    *    *    mon  → 每周一上午 9 点
*/30  *    *    *    *    → 每 30 分钟
```

---

## 🔍 六、故障排查

### 6.1 常见问题

**问题 1: ModuleNotFoundError: No module named 'mysql'**

解决：
```bash
pip install mysql-connector-python
```

**问题 2: ModuleNotFoundError: No module named 'apscheduler'**

解决：
```bash
pip install apscheduler
```

**问题 3: MySQL 连接失败**

检查：
- MySQL 服务是否运行
- 端口是否正确（默认 3307）
- 用户名密码是否正确
- 数据库是否已创建

**问题 4: ETL 执行失败**

检查：
- 日志文件：`logs/etl/etl_*.log`
- 数据源表是否存在
- 数据是否符合预期格式

### 6.2 调试模式

启用详细日志：

```bash
export ETL_LOG_LEVEL=DEBUG
python3 run_etl.py
```

---

## 📈 七、性能优化

### 7.1 批量处理

调整批量大小：

```bash
export ETL_BATCH_SIZE=2000  # 默认 1000
```

### 7.2 并发执行

调整线程池大小：

```bash
export SCHEDULER_THREADS=20  # 默认 10
```

### 7.3 数据库索引

确保以下索引已创建：

```sql
-- ODS 层索引
CREATE INDEX idx_ods_room_dt ON ods_room(dt);
CREATE INDEX idx_ods_trade_dt ON ods_trade(dt);
CREATE INDEX idx_ods_payment_dt ON ods_payment(dt);

-- DWD 层索引
CREATE INDEX idx_dwd_room_dt ON dwd_room_detail(dt);
CREATE INDEX idx_dwd_trade_dt ON dwd_trade_detail(dt);

-- DWS 层索引
CREATE INDEX idx_dws_fact_dt ON dws_sales_payment_fact(dt);
```

---

## 📝 八、下一步

1. **数据迁移**: 将现有业务数据迁移到数仓
2. **API 集成**: 更新 `api_admin/etl_jobs.py` 以集成新调度器
3. **监控告警**: 实现 ETL 失败告警（邮件/短信）
4. **数据质量**: 完善数据质量检查规则
5. **性能调优**: 根据实际数据量优化 ETL 性能

---

## 📚 九、参考资料

- [ETL_SCHEDULER_MANUAL.md](./ETL_SCHEDULER_MANUAL.md) - 详细使用手册
- 黄强论文《基于 ERP 的地产行业商业智能报表系统的设计与实现》
- [APScheduler 文档](https://apscheduler.readthedocs.io/)
- [MySQL 文档](https://dev.mysql.com/doc/)

---

**创建时间：** 2026-03-19  
**创建人员：** mac🦀  
**状态：** ✅ 已完成
