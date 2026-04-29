# AI数据融合 数据仓库 ETL 流程与调度系统

**基于黄强论文《基于 ERP 的地产行业商业智能报表系统的设计与实现》**

---

## 📋 一、系统概述

本系统实现了完整的地产行业 BI 数据仓库 ETL 流程和调度系统，严格遵循黄强论文中的数仓分层设计（ODS/DWD/DWS/ADS 四层架构）。

### 1.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                       数据源层                               │
│     明源云 ERP  │   SAP ERP   │   线下 Excel  │            │
└────────┬──────────┴─────┬─────┴──────┬─────────────────────┘
         │                 │            │
         ▼                 ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│              ODS 层（操作数据层）- 9 张表                      │
│  ods_room, ods_trade, ods_payment, ods_pay, ...           │
│  [抽取策略：全量/增量]                                      │
└────────────────────────┬────────────────────────────────────┘
                         │ ETL Extract
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              DWD 层（明细数据层）- 7 张表                      │
│  dwd_room_detail, dwd_trade_detail, ...                   │
│  [清洗策略：编码统一、格式转换、异常处理]                    │
└────────────────────────┬────────────────────────────────────┘
                         │ ETL Transform
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              DWS 层（服务数据层）- 5 张表                      │
│  dws_sales_payment_fact, dws_sales_cost_fact,             │
│  dim_project, dim_date, dim_account                        │
│  [聚合策略：主题聚合、维度关联]                              │
└────────────────────────┬────────────────────────────────────┘
                         │ ETL Load
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ADS 层（应用数据层）- 7 张表                      │
│  ads_group_sales_report, ads_sales_dashboard,             │
│  ads_finance_dashboard, ads_szl_dashboard                 │
│  [报表策略：按报表口径二次聚合]                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              调度系统 (APScheduler)                          │
│  - 定时调度（Cron）                                         │
│  - 手动触发                                                 │
│  - 任务监控                                                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 数仓分层表清单

| 层级 | 表数量 | 表名 |
|------|--------|------|
| **ODS** | 9 | ods_room, ods_trade, ods_payment, ods_pay, ods_account, ods_contract, ods_bseg, ods_gl_actual, ods_other |
| **DWD** | 7 | dwd_room_detail, dwd_trade_detail, dwd_payment_detail, dwd_contract_detail, dwd_pay_detail, dwd_gl_actual_detail, dwd_gl_budget_detail |
| **DWS** | 5 | dws_sales_payment_fact, dws_sales_cost_fact, dim_project, dim_date, dim_account |
| **ADS** | 7 | ads_group_sales_report, ads_group_salesdate_report, ads_group_pay_report, ads_project_cost_report, ads_sales_dashboard, ads_finance_dashboard, ads_szl_dashboard |
| **总计** | **28** | |

---

## 📁 二、目录结构

```
backend/
├── etl/                          # ETL 核心模块
│   ├── __init__.py
│   ├── config.py                 # ETL 配置管理
│   ├── utils.py                  # 工具函数（连接、重试、质量检查）
│   ├── extractors/               # 数据抽取器
│   │   ├── __init__.py
│   │   └── ods_extractor.py      # ODS 层抽取
│   ├── transformers/             # 数据转换器
│   │   ├── __init__.py
│   │   ├── dwd_cleaner.py        # DWD 层清洗
│   │   └── dws_aggregator.py     # DWS 层聚合
│   └── loaders/                  # 数据加载器
│       ├── __init__.py
│       └── ads_loader.py         # ADS 层报表生成
│
├── scheduler/                    # 调度系统
│   ├── __init__.py
│   ├── config.py                 # 调度器配置
│   ├── jobs.py                   # 任务定义
│   └── scheduler.py              # 调度器主程序
│
├── api_admin/
│   └── etl_jobs.py               # ETL 管理 API（更新版）
│
├── logs/
│   └── etl/                      # ETL 执行日志
│       └── etl_YYYY-MM-DD.log
│
└── db/
    └── init_warehouse_mysql.sql  # 数仓表结构（30 张表）
```

---

## 🚀 三、快速开始

### 3.1 环境准备

```bash
# 安装依赖
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system/backend
pip install apscheduler mysql-connector-python

# 配置环境变量
export MYSQL_HOST=localhost
export MYSQL_PORT=3307
export MYSQL_USER=erp_bi
export MYSQL_PASSWORD=erp_bi123
export MYSQL_DATABASE=erp_bi_warehouse
export SQLITE_DB_PATH=db/erp_bi.db
export ETL_MODE=incremental  # full 或 incremental
```

### 3.2 手动执行 ETL

```bash
# 执行完整 ETL 流程
python -m etl_pipeline

# 或分步执行
python -c "from etl.extractors.ods_extractor import run_ods_extraction; run_ods_extraction()"
python -c "from etl.transformers.dwd_cleaner import run_dwd_cleaning; run_dwd_cleaning()"
python -c "from etl.transformers.dws_aggregator import run_dws_aggregation; run_dws_aggregation()"
python -c "from etl.loaders.ads_loader import run_ads_loading; run_ads_loading()"
```

### 3.3 启动调度器

```bash
# 启动调度器（后台运行）
python scheduler/scheduler.py start

# 查看状态
python scheduler/scheduler.py status

# 停止调度器
python scheduler/scheduler.py stop
```

### 3.4 使用 API 管理

```bash
# 启动 API 服务
python main_new.py

# API 文档
http://localhost:8000/docs
```

---

## ⚙️ 四、配置说明

### 4.1 ETL 配置（etl/config.py）

```python
# 数据库配置
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3307
MYSQL_USER = 'erp_bi'
MYSQL_PASSWORD = 'erp_bi123'
MYSQL_DATABASE = 'erp_bi_warehouse'

# ETL 模式
ETL_MODE = 'incremental'  # full | incremental
ETL_MAX_RETRIES = 3
ETL_RETRY_DELAY = 5
ETL_BATCH_SIZE = 1000

# 分区日期（T+1）
DT = date.today() - timedelta(days=1)
```

### 4.2 调度配置（scheduler/config.py）

```python
# 调度器类型
SCHEDULER_TYPE = 'background'
SCHEDULER_TIMEZONE = 'Asia/Shanghai'

# 持久化
SCHEDULER_PERSISTENT = False
DATABASE_URL = 'sqlite:///logs/scheduler.db'

# 线程池
SCHEDULER_THREADS = 10
SCHEDULER_PROCESSES = 2
```

### 4.3 默认调度计划

| 任务 | Cron 表达式 | 说明 |
|------|-----------|------|
| 完整 ETL 流程 | `0 1 * * mon` | 每周一凌晨 1 点 |
| ODS 抽取 | `0 2 * * *` | 每天凌晨 2 点 |
| DWD 清洗 | `0 3 * * *` | 每天凌晨 3 点 |
| DWS 聚合 | `0 4 * * *` | 每天凌晨 4 点 |
| ADS 报表 | `0 5 * * *` | 每天凌晨 5 点 |
| 维度表刷新 | `0 3 * * sun` | 每周日凌晨 3 点 |

---

## 📊 五、ETL 流程详解

### 5.1 ODS 层抽取（Extract）

**文件：** `etl/extractors/ods_extractor.py`

**功能：**
- 从 SQLite 业务库抽取原始数据
- 映射到 MySQL ODS 层表
- 支持全量和增量两种模式
- 添加分区日期（dt）字段

**抽取策略：**
```python
# 全量抽取：清空目标表后重新加载
TRUNCATE TABLE ods_room;
INSERT INTO ods_room ... SELECT * FROM re_units;

# 增量抽取：仅抽取 T+1 数据
INSERT INTO ods_room ... 
SELECT * FROM re_units 
WHERE created_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY);
```

### 5.2 DWD 层清洗（Transform）

**文件：** `etl/transformers/dwd_cleaner.py`

**功能：**
- 数据标准化（空值处理、格式统一）
- 编码统一（跨系统映射）
- 异常数据处理（去重、合理性校验）
- 关联维度表（补充项目名称等）

**清洗规则：**
```sql
-- 示例：房源明细清洗
INSERT INTO dwd_room_detail
SELECT 
    CONCAT('RK_', COALESCE(room_guid, 'UNKNOWN')) as room_key,
    COALESCE(project_name, '未知项目') as project_name,
    COALESCE(room_status, 'unknown') as room_status,
    COALESCE(total_price, 0) as total_price,
    ...
FROM ods_room
WHERE dt = '2026-03-18'
AND room_guid IS NOT NULL;
```

### 5.3 DWS 层聚合（Aggregate）

**文件：** `etl/transformers/dws_aggregator.py`

**功能：**
- 销售 - 回款事实表聚合
- 成本 - 费用事实表聚合
- 维度表构建（项目、时间、科目）

**聚合示例：**
```sql
-- 销售 - 回款事实表
INSERT INTO dws_sales_payment_fact
SELECT 
    project_guid,
    contract_guid,
    SUM(contract_amount) as contract_amount,
    SUM(payment_amount) as payment_amount,
    ROUND(SUM(payment_amount) * 100.0 / SUM(contract_amount), 2) as payment_rate,
    ...
FROM dwd_trade_detail
LEFT JOIN dwd_payment_detail USING (contract_guid)
GROUP BY project_guid, contract_guid;
```

### 5.4 ADS 层报表（Load）

**文件：** `etl/loaders/ads_loader.py`

**功能：**
- 集团销售目标达成报表
- 集团签约回款周月年报
- 集团费用支出汇总
- 项目成本费用报表
- 营销/财务/收支利驾驶舱

**报表示例：**
```sql
-- 营销驾驶舱
INSERT INTO ads_sales_dashboard
SELECT 
    project_guid,
    COUNT(*) as total_units,
    SUM(CASE WHEN room_status = 'signed' THEN 1 ELSE 0 END) as sold_units,
    ROUND(sold_units * 100.0 / total_units, 2) as sell_through_rate,
    SUM(total_price) as total_sales,
    ...
FROM dwd_room_detail
GROUP BY project_guid;
```

---

## 🔧 六、API 接口

### 6.1 ETL 任务管理

**GET** `/api/admin/etl/tasks`
- 获取 ETL 任务列表
- 参数：`layer`（筛选 ODS/DWD/DWS/ADS）

**POST** `/api/admin/etl/tasks/{task_id}/run`
- 手动触发 ETL 任务
- 返回：执行结果

**GET** `/api/admin/etl/tasks/{task_id}/log`
- 查看任务执行日志
- 参数：`page`, `page_size`

### 6.2 调度配置管理

**GET** `/api/admin/etl/schedules`
- 获取调度配置列表

**POST** `/api/admin/etl/schedules`
- 创建调度配置
- 请求体：`task_name`, `cron_expression`, `is_enabled`

**PUT** `/api/admin/etl/schedules/{schedule_id}`
- 更新调度配置

**DELETE** `/api/admin/etl/schedules/{schedule_id}`
- 删除调度配置

### 6.3 调度器控制

**POST** `/api/admin/etl/scheduler/start`
- 启动调度器

**POST** `/api/admin/etl/scheduler/stop`
- 停止调度器

**GET** `/api/admin/etl/scheduler/status`
- 获取调度器状态

**POST** `/api/admin/etl/scheduler/jobs/{job_id}/pause`
- 暂停任务

**POST** `/api/admin/etl/scheduler/jobs/{job_id}/resume`
- 恢复任务

---

## 📈 七、监控与告警

### 7.1 执行日志

日志文件：`logs/etl/etl_YYYY-MM-DD.log`

**日志格式：**
```
2026-03-19 02:00:00 - INFO - 🚀 ETL 流程开始
2026-03-19 02:00:01 - INFO - 📤 开始抽取房源数据...
2026-03-19 02:00:05 - INFO - ✅ 抽取 1000 条房源数据到 ods_room
2026-03-19 02:00:06 - INFO - ✅ ETL 流程完成
```

### 7.2 数据质量检查

**检查项：**
- 空值检查
- 主键唯一性检查
- 数据范围检查
- 参照完整性检查

**使用示例：**
```python
from etl.utils import DataQualityChecker

checker = DataQualityChecker()
checker.check_null_values(data, ['room_guid'], 'ods_room')
checker.check_duplicate_keys(data, 'room_guid', 'ods_room')
report = checker.get_report()
```

### 7.3 错误处理

- 自动重试机制（最多 3 次）
- 失败告警（日志记录）
- 事务回滚（保证数据一致性）

---

## 📖 八、使用手册

### 8.1 新增 ETL 任务

1. 在 `scheduler/jobs.py` 中定义任务函数：

```python
@etl_task('新任务名称')
def job_new_task() -> Dict[str, Any]:
    # 任务逻辑
    return {'success': True}
```

2. 在 `TASK_REGISTRY` 中注册：

```python
TASK_REGISTRY = {
    'new_task': {
        'func': job_new_task,
        'name': '新任务',
        'layer': 'ODS',
        'description': '任务描述',
        'default_schedule': {'hour': 2, 'minute': 0}
    }
}
```

### 8.2 自定义调度计划

**通过 API：**
```bash
curl -X POST http://localhost:8000/api/admin/etl/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "ODS 数据抽取",
    "cron_expression": "0 2 * * *",
    "is_enabled": true
  }'
```

**通过代码：**
```python
from scheduler import get_scheduler

scheduler = get_scheduler()
scheduler.add_job(
    task_id='ods_extraction',
    trigger='cron',
    cron_expr='0 2 * * *',
    job_id='custom_ods_job'
)
```

### 8.3 故障排查

**问题 1：ETL 执行失败**
- 检查日志：`logs/etl/etl_*.log`
- 检查数据库连接
- 检查数据源表是否存在

**问题 2：调度器未启动**
- 检查 APScheduler 是否安装
- 检查端口是否被占用
- 查看调度器状态：`python scheduler.py status`

**问题 3：数据不一致**
- 检查 ETL 执行顺序（ODS→DWD→DWS→ADS）
- 检查分区日期（dt）是否一致
- 查看数据质量检查报告

---

## 🧪 九、测试验证

### 9.1 单元测试

```bash
# 运行测试
pytest tests/test_etl.py -v
```

### 9.2 集成测试

```python
# 测试完整 ETL 流程
from etl import run_full_etl

result = run_full_etl(mode='incremental')
assert result['success'] == True
```

### 9.3 性能测试

```python
# 测试百万级数据抽取
import time
from etl.extractors.ods_extractor import ODSExtractor

start = time.time()
extractor = ODSExtractor()
extractor.extract_rooms()
end = time.time()

print(f"抽取耗时：{end - start:.2f}秒")
```

---

## 📝 十、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-19 | 初始版本，实现完整 ETL 流程和调度系统 |

---

## 📚 十一、参考资料

1. 黄强论文《基于 ERP 的地产行业商业智能报表系统的设计与实现》
2. APScheduler 官方文档：https://apscheduler.readthedocs.io/
3. MySQL 官方文档：https://dev.mysql.com/doc/

---

**实施完成时间：** 2026-03-19  
**实施人员：** mac🦀  
**实施状态：** ✅ 已完成
