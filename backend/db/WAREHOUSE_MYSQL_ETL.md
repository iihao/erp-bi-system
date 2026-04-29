# 地产行业 BI 数据仓库 + ETL 实施报告

**实施时间：** 2026-03-18  
**实施人员：** mac🦀  
**论文依据：** 黄强《基于 ERP 的地产行业商业智能报表系统的设计与实现》

---

## 📋 一、实施概述

本次实施基于论文设计，完成了以下工作：

1. ✅ **MySQL 数据仓库搭建**（Docker Compose）
2. ✅ **30 张数仓表 DDL 设计**（ODS/DWD/DWS/ADS 四层）
3. ✅ **ETL 流程框架开发**（Python 实现）
4. ✅ **数据分区策略**（dt 字段支持 T+1 增量）

---

## 🏗️ 二、技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    数据源层                              │
│  明源云 ERP  │   SAP ERP   │   线下 Excel  │  现有 SQLite │
└──────┬──────────┴──────┬──────┴───────┬────────┬───────┘
       │                  │               │        │
       ▼                  ▼               ▼        ▼
┌─────────────────────────────────────────────────────────┐
│              ETL 抽取层（Python）                        │
│  数据抽取 → 数据清洗 → 数据转换 → 数据加载              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│         MySQL 8.0 数据仓库（Docker 容器）                │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ODS 层 (9 表)  │  原始数据，保持原貌            │   │
│  │  DWD 层 (7 表)  │  清洗后的明细数据              │   │
│  │  DWS 层 (5 表)  │  主题聚合宽表                  │   │
│  │  ADS 层 (7 表)  │  报表应用数据集                │   │
│  │  维度表 (5 表)  │  项目/时间/科目/权限/指标      │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              应用层                                      │
│  BI 报表  │  管理驾驶舱  │  RPA 派发  │  API 接口       │
└─────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| **数仓数据库** | MySQL 8.0 | Docker 容器运行，端口 3307 |
| **业务数据库** | SQLite | 现有系统继续使用 |
| **ETL 工具** | Python + mysql-connector | 自定义 ETL 脚本 |
| **数据分区** | dt 字段（DATE 类型） | 支持 T+1 增量加载 |
| **字符集** | utf8mb4 | 支持中文和 emoji |

---

## 📦 三、文件清单

### 3.1 Docker 配置
- `docker-compose-warehouse.yml` - MySQL 数仓容器编排
- `.env` - 环境变量配置（密码等敏感信息）

### 3.2 数据库脚本
- `backend/db/init_warehouse_mysql.sql` - MySQL 数仓 30 张表完整 DDL
- `backend/db/init_warehouse_tables.sql` - SQLite 版本（保留参考）
- `backend/db/init_real_estate_tables.sql` - 前期 10 张业务表（保留）

### 3.3 ETL 脚本
- `backend/etl_pipeline.py` - ETL 主流程（Python）
- `backend/logs/etl.log` - ETL 执行日志

### 3.4 文档
- `backend/db/WAREHOUSE_SCHEMA.md` - 前期实施报告（SQLite 版）
- `backend/db/WAREHOUSE_MYSQL_ETL.md` - 本文档（MySQL+ETL 完整版）

---

## 🚀 四、部署步骤

### 4.1 启动 MySQL 数仓

```bash
# 1. 进入项目目录
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system

# 2. 设置环境变量（可选）
export MYSQL_ROOT_PASSWORD=root123
export MYSQL_PASSWORD=erp_bi123

# 3. 启动 MySQL 容器
docker-compose -f docker-compose-warehouse.yml up -d

# 4. 查看容器状态
docker ps | grep erp_bi_warehouse

# 5. 查看日志
docker logs -f erp_bi_warehouse
```

### 4.2 验证数仓表创建

```bash
# 连接 MySQL 数仓
docker exec -it erp_bi_warehouse mysql -uerp_bi -perp_bi123 erp_bi_warehouse

# 执行验证查询
SELECT 'ODS 层' AS layer, COUNT(*) AS table_count FROM information_schema.tables 
WHERE table_schema = DATABASE() AND table_name LIKE 'ods_%'
UNION ALL
SELECT 'DWD 层', COUNT(*) FROM information_schema.tables 
WHERE table_schema = DATABASE() AND table_name LIKE 'dwd_%'
UNION ALL
SELECT 'DWS 层', COUNT(*) FROM information_schema.tables 
WHERE table_schema = DATABASE() AND table_name LIKE 'dws_%'
UNION ALL
SELECT 'ADS 层', COUNT(*) FROM information_schema.tables 
WHERE table_schema = DATABASE() AND table_name LIKE 'ads_%'
UNION ALL
SELECT '维度表', COUNT(*) FROM information_schema.tables 
WHERE table_schema = DATABASE() AND table_name LIKE 'dim_%';
```

**预期结果：**
```
+--------+--------------+
| layer  | table_count  |
+--------+--------------+
| ODS 层 |            9 |
| DWD 层 |            7 |
| DWS 层 |            2 |
| ADS 层 |            7 |
| 维度表 |            5 |
+--------+--------------+
```

### 4.3 安装 Python 依赖

```bash
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system/backend

# 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install mysql-connector-python
```

### 4.4 执行 ETL 流程

```bash
# 1. 进入后端目录
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system/backend

# 2. 设置环境变量
export MYSQL_HOST=localhost
export MYSQL_PORT=3307
export MYSQL_USER=erp_bi
export MYSQL_PASSWORD=erp_bi123
export MYSQL_DATABASE=erp_bi_warehouse

# 3. 执行 ETL
python etl_pipeline.py

# 4. 查看日志
tail -f logs/etl.log
```

---

## 📊 五、数仓表设计详情

### 5.1 ODS 层（9 张表）

**设计原则：** 保持源系统数据结构，几乎不做清洗和转换

| 表名 | 中文名 | 数据来源 | 分区字段 | 说明 |
|------|--------|---------|---------|------|
| `ods_room` | 房间明细表 | 明源云 ERP | dt | 记录各项目所有房源信息 |
| `ods_trade` | 销售表 | 明源云 ERP | dt | 记录客户签订售房合同明细 |
| `ods_payment` | 回款明细表 | 明源云 ERP | dt | 记录回款明细（按揭 + 公积金） |
| `ods_pay` | 付款登记表 | 明源云 ERP | dt | 合同付款、对公请款、发票报销 |
| `ods_account` | 科目表 | 明源云 ERP | dt | 财务科目，与成本费用对应 |
| `ods_contract` | 合同表 | 明源云 ERP | dt | 成本费用产生过程中的合同 |
| `ods_bseg` | 凭证表 | SAP ERP | dt | 财务凭证明细（行项目） |
| `ods_gl_actual` | 总账实际业务表 | SAP ERP | dt | 总账模块实际业务数据 |
| `ods_other` | 其他数据表 | Excel 填报 | dt | 手动填报数据 |

**关键字段：**
- 主键：各表业务主键（如 room_guid, trade_guid 等）
- 分区字段：`dt DATE` - 数据分区日期
- 审计字段：`created_at TIMESTAMP`

### 5.2 DWD 层（7 张表）

**设计原则：** 数据清洗、标准化、去除冗余

| 表名 | 中文名 | 数据来源 | 清洗规则 |
|------|--------|---------|---------|
| `dwd_room_detail` | 房源明细表 | ods_room | 补全项目名称、统一状态编码 |
| `dwd_trade_detail` | 销售明细表 | ods_trade | 去重、客户信息标准化 |
| `dwd_payment_detail` | 回款明细表 | ods_payment | 去除无效和重复记录 |
| `dwd_contract_detail` | 合同明细表 | ods_contract | 合同金额、科目标准化 |
| `dwd_pay_detail` | 付款明细表 | ods_pay | 无合同付款处理 |
| `dwd_gl_actual_detail` | 总账实际明细表 | ods_gl_actual | SAP 数据标准化 |
| `dwd_gl_budget_detail` | 总账预算明细表 | - | 预算数据清洗 |

**关键字段：**
- 代理主键：`{table}_key VARCHAR(64)` - 如 room_key, trade_key
- 数据版本：`data_version DATE` - 标识数据版本
- 分区字段：`dt DATE`

### 5.3 DWS 层（5 张表）

**设计原则：** 面向分析主题，事实表 + 维度表

| 表名 | 中文名 | 类型 | 说明 |
|------|--------|------|------|
| `dws_sales_payment_fact` | 销售 - 回款事实表 | 事实表 | 聚合合同销售与回款 |
| `dws_sales_cost_fact` | 成本 - 费用事实表 | 事实表 | 聚合合同付款及费用 |
| `dim_project` | 项目维度表 | 维度表 | 项目信息（区域/业态/楼栋） |
| `dim_date` | 时间维度表 | 维度表 | 年月日分层时间信息 |
| `dim_account` | 科目维度表 | 维度表 | 财务科目信息 |

**核心指标：**
- 合同金额、回款金额、回款率
- 成本金额、费用金额、预算差异
- 合同数量、回款数量

### 5.4 ADS 层（7 张表）

**设计原则：** 适配报表需求，按报表口径二次聚合

| 表名 | 中文名 | 对应报表 | 说明 |
|------|--------|---------|------|
| `ads_group_sales_report` | 集团销售目标达成表 | 集团销售进度分析 | 目标 vs 实际 |
| `ads_group_salesdate_report` | 集团签约回款周月年报 | 销售周报/月报/年报 | 签约 + 回款 |
| `ads_group_pay_report` | 集团费用支出汇总表 | 高层决策支持 | 合同支出 + 三费 |
| `ads_project_cost_report` | 项目成本费用报表 | 项目成本控制 | 预算执行分析 |
| `ads_sales_dashboard` | 营销驾驶舱大屏 | 管理驾驶舱 | 销售去化率 |
| `ads_finance_dashboard` | 财务驾驶舱大屏 | 管理驾驶舱 | 财务 KPI |
| `ads_szl_dashboard` | 收支利大屏 | 综合分析大屏 | 销售 + 成本 + 利润 |

### 5.5 维度表（5 张表）

| 表名 | 中文名 | 说明 |
|------|--------|------|
| `dim_project` | 项目维度表 | 项目主数据 |
| `dim_date` | 时间维度表 | 日期维度（年季月日） |
| `dim_account` | 科目维度表 | 财务科目树 |
| `dim_permission` | 权限控制表 | 行级权限控制 |
| `dim_indicator` | 指标口径库 | 统一指标定义 |

---

## 🔄 六、ETL 流程详解

### 6.1 ETL 四层加工策略

| ETL 阶段 | 数仓层级 | 加工目标 | 核心技术策略 |
|---------|---------|---------|-------------|
| **数据源→ODS 层** | ODS | 暂存原始数据，保留数据原貌 | 全量抽取、增量抽取、共享加载 |
| **ODS 层→DWD 层** | DWD | 数据清洗、标准化，消除冗余 | 编码统一、格式统一、空值/重复值剔除 |
| **DWD 层→DWS 层** | DWS | 主题化聚合，构建业务宽表 | 关联维度表、计算核心指标 |
| **DWS 层→ADS 层** | ADS | 适配报表需求，生成最终数据集 | 按报表口径二次聚合 |

### 6.2 ETL 脚本结构

```python
ETLPipeline
├── ETLConnection         # 数据库连接管理
│   ├── connect_sqlite()  # 连接 SQLite 业务库
│   └── connect_mysql()   # 连接 MySQL 数仓
├── ETLExtractor          # 数据抽取器
│   ├── extract_projects()
│   ├── extract_buildings()
│   ├── extract_units()
│   ├── extract_customers()
│   ├── extract_contracts()
│   └── extract_payments()
├── ETLLoader             # 数据加载器
│   ├── load_to_ods()     # 加载到 ODS 层
│   ├── execute_sql()     # 执行 SQL
│   └── truncate_table()  # 清空表
└── run()                 # 主流程
    ├── etl_source_to_ods()   # 阶段 1：业务库→ODS
    ├── etl_odsto_dwd()       # 阶段 2：ODS→DWD（清洗）
    ├── etl_dwd_to_dws()      # 阶段 3：DWD→DWS（聚合）
    └── etl_dws_to_ads()      # 阶段 4：DWS→ADS（报表）
```

### 6.3 ETL 执行示例

#### 阶段 1：业务库 → ODS 层

```sql
-- 示例：从 SQLite re_units 抽取到 MySQL ods_room
INSERT INTO ods_room 
(room_guid, project_guid, building_code, room_code, room_name, 
 floor, unit_number, room_type, building_area, internal_area, 
 share_area, orientation, total_price, unit_price, room_status, dt)
SELECT 
    unit_guid, building_id, building_code, unit_code, unit_name,
    floor, unit_number, unit_type, building_area, internal_area,
    share_area, orientation, total_price, unit_price, unit_status,
    DATE(NOW())
FROM sqlite_erp_bi.re_units;
```

#### 阶段 2：ODS 层 → DWD 层（数据清洗）

```sql
-- 示例：房源数据清洗
INSERT INTO dwd_room_detail
(room_key, room_guid, project_guid, project_name, building_code, 
 room_code, room_name, floor, unit_number, room_type, 
 building_area, internal_area, share_area, orientation, 
 total_price, unit_price, room_status, data_version, dt)
SELECT 
    CONCAT('RK_', room_guid),
    room_guid,
    o.project_guid,
    p.project_name,  -- 从项目维度表补全
    o.building_code,
    o.room_code,
    o.room_name,
    o.floor,
    o.unit_number,
    CASE o.room_type
        WHEN '1' THEN '1 室 1 厅'
        WHEN '2' THEN '2 室 2 厅'
        WHEN '3' THEN '3 室 2 厅'
        ELSE o.room_type
    END,
    o.building_area,
    o.internal_area,
    o.share_area,
    o.orientation,
    o.total_price,
    o.unit_price,
    CASE o.room_status
        WHEN 'available' THEN '可售'
        WHEN 'reserved' THEN '已预订'
        WHEN 'signed' THEN '已签约'
        WHEN 'delivered' THEN '已交付'
        ELSE o.room_status
    END,
    DATE(NOW()),
    o.dt
FROM ods_room o
LEFT JOIN dim_project p ON o.project_guid = p.project_guid
WHERE o.dt = '2026-03-18';
```

#### 阶段 3：DWD 层 → DWS 层（主题聚合）

```sql
-- 示例：销售 - 回款事实表聚合
INSERT INTO dws_sales_payment_fact
(project_guid, project_name, contract_guid, customer_guid,
 date_key, year, month, day, contract_amount, payment_amount,
 payment_rate, contract_count, payment_count, data_version, dt)
SELECT 
    d.project_guid,
    d.project_name,
    d.contract_guid,
    d.customer_guid,
    d.contract_sign_date,
    YEAR(d.contract_sign_date),
    MONTH(d.contract_sign_date),
    DAY(d.contract_sign_date),
    SUM(d.total_price),
    COALESCE(SUM(p.payment_amount), 0),
    CASE 
        WHEN SUM(d.total_price) > 0 
        THEN COALESCE(SUM(p.payment_amount), 0) * 100.0 / SUM(d.total_price)
        ELSE 0 
    END,
    COUNT(DISTINCT d.contract_guid),
    COUNT(DISTINCT p.payment_guid),
    DATE(NOW()),
    d.dt
FROM dwd_trade_detail d
LEFT JOIN dwd_payment_detail p ON d.contract_guid = p.contract_guid
WHERE d.dt = '2026-03-18'
GROUP BY d.project_guid, d.project_name, d.contract_guid, d.customer_guid,
         d.contract_sign_date;
```

#### 阶段 4：DWS 层 → ADS 层（报表聚合）

```sql
-- 示例：营销驾驶舱聚合
INSERT INTO ads_sales_dashboard
(dashboard_date, project_guid, project_name, total_units, sold_units,
 available_units, sell_through_rate, total_sales, total_payment,
 payment_rate, avg_unit_price, data_version, dt)
SELECT 
    DATE(NOW()),
    project_guid,
    project_name,
    COUNT(*),
    SUM(CASE WHEN room_status IN ('已签约', '已交付') THEN 1 ELSE 0 END),
    SUM(CASE WHEN room_status = '可售' THEN 1 ELSE 0 END),
    ROUND(
        SUM(CASE WHEN room_status IN ('已签约', '已交付') THEN 1 ELSE 0 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 2
    ),
    SUM(total_price),
    0,  -- 待计算
    0,  -- 待计算
    AVG(unit_price),
    DATE(NOW()),
    dt
FROM dwd_room_detail
WHERE dt = '2026-03-18'
GROUP BY project_guid, project_name;
```

---

## 📅 七、数据分区策略

### 7.1 分区字段设计

所有数仓表均包含 `dt DATE` 字段，用于数据分区：

```sql
-- 示例表结构
CREATE TABLE ods_room (
    ...
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dt (dt)
);
```

### 7.2 增量加载策略

```bash
# T+1 增量加载示例
# 每天凌晨 2 点执行，加载前一天的数据

# 1. 抽取 T-1 日的业务数据
export ETL_DATE=$(date -d "yesterday" +%Y-%m-%d)

# 2. 执行 ETL
python etl_pipeline.py --date $ETL_DATE

# 3. 验证数据
docker exec -it erp_bi_warehouse mysql -uerp_bi -perp_bi123 erp_bi_warehouse -e \
  "SELECT dt, COUNT(*) FROM ods_room WHERE dt='$ETL_DATE' GROUP BY dt;"
```

### 7.3 数据保留策略

| 层级 | 保留策略 | 清理频率 |
|------|---------|---------|
| ODS 层 | 永久保留（原始数据） | 不清理 |
| DWD 层 | 保留最近 3 年 | 每年清理 |
| DWS 层 | 保留最近 2 年 | 每半年清理 |
| ADS 层 | 保留最近 1 年 | 每月清理 |

---

## 🔐 八、权限控制

### 8.1 数据库用户权限

```sql
-- 创建只读用户（报表查询）
CREATE USER 'erp_bi_reader'@'%' IDENTIFIED BY 'reader123';
GRANT SELECT ON erp_bi_warehouse.* TO 'erp_bi_reader'@'%';

-- 创建 ETL 用户（数据加载）
CREATE USER 'erp_bi_etl'@'%' IDENTIFIED BY 'etl123';
GRANT SELECT, INSERT, UPDATE ON erp_bi_warehouse.* TO 'erp_bi_etl'@'%';

-- 创建管理员用户（DDL 操作）
CREATE USER 'erp_bi_admin'@'%' IDENTIFIED BY 'admin123';
GRANT ALL PRIVILEGES ON erp_bi_warehouse.* TO 'erp_bi_admin'@'%';
```

### 8.2 行级权限控制（论文 5.2 节）

```sql
-- 权限表示例
INSERT INTO dim_permission (user_id, role_id, department_id, project_guid, permission_key, data_scope) VALUES
('user001', 'role_project_manager', 'dept_shanghai', 'proj_001', 'project_view', 'proj_001'),
('user002', 'role_city_manager', 'dept_shanghai', NULL, 'city_view', 'city_shanghai'),
('user003', 'role_group_admin', NULL, NULL, 'group_view', 'all');
```

---

## 📈 九、性能优化

### 9.1 索引策略

每个表都创建了以下索引：
- 主键索引（PRIMARY KEY）
- 外键索引（如 project_guid, contract_guid）
- 分区字段索引（dt）
- 查询字段索引（status, date 等）

### 9.2 分区表（可选）

对于大数据量表，可以使用 MySQL 分区：

```sql
-- 示例：按 dt 字段进行 RANGE 分区
ALTER TABLE ods_trade
PARTITION BY RANGE (YEAR(dt)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027)
);
```

### 9.3 物化视图（可选）

对于频繁查询的 ADS 层数据，可以创建物化视图：

```sql
-- 创建物化视图（需要手动刷新）
CREATE TABLE ads_sales_dashboard_mv AS
SELECT ... FROM dwd_room_detail GROUP BY project_guid;

-- 定期刷新
INSERT INTO ads_sales_dashboard_mv 
SELECT ... FROM dwd_room_detail 
WHERE dt = CURDATE()
ON DUPLICATE KEY UPDATE ...;
```

---

## 🧪 十、测试验证

### 10.1 数据完整性验证

```sql
-- 验证 ODS 层数据量
SELECT 'ods_room' AS table_name, COUNT(*) AS row_count FROM ods_room
UNION ALL
SELECT 'ods_trade', COUNT(*) FROM ods_trade
UNION ALL
SELECT 'ods_payment', COUNT(*) FROM ods_payment;

-- 验证 DWD 层数据量
SELECT 'dwd_room_detail' AS table_name, COUNT(*) AS row_count FROM dwd_room_detail
UNION ALL
SELECT 'dwd_trade_detail', COUNT(*) FROM dwd_trade_detail;

-- 验证数据一致性（ODS vs DWD）
SELECT 
    (SELECT COUNT(*) FROM ods_room WHERE dt='2026-03-18') AS ods_count,
    (SELECT COUNT(*) FROM dwd_room_detail WHERE dt='2026-03-18') AS dwd_count;
```

### 10.2 指标验证

```sql
-- 验证销售去化率
SELECT 
    project_name,
    COUNT(*) AS total_units,
    SUM(CASE WHEN room_status IN ('已签约', '已交付') THEN 1 ELSE 0 END) AS sold_units,
    ROUND(SUM(CASE WHEN room_status IN ('已签约', '已交付') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS sell_through_rate
FROM dwd_room_detail
WHERE dt = '2026-03-18'
GROUP BY project_name;
```

---

## 📝 十一、后续工作

### 11.1 待完成事项

- [ ] 完善 ETL 脚本中的字段映射逻辑
- [ ] 实现完整的 ODS→DWD 清洗规则
- [ ] 实现 DWD→DWS 聚合逻辑
- [ ] 实现 DWS→ADS 报表聚合逻辑
- [ ] 添加数据质量检查（空值、重复、异常值）
- [ ] 实现 ETL 失败告警（邮件/钉钉）
- [ ] 添加 ETL 调度（Airflow/Crontab）

### 11.2 数据迁移

将现有 SQLite 业务数据迁移到 MySQL 数仓：

```bash
# 执行数据迁移脚本
python migrate_sqlite_to_mysql.py
```

### 11.3 报表开发

基于 ADS 层数据开发报表：
- 集团销售目标达成报表
- 项目去化率分析报表
- 财务驾驶舱大屏
- 营销驾驶舱大屏

---

## 🎓 十二、总结

本次实施严格遵循黄强论文设计，完成了：

1. ✅ **MySQL 数据仓库搭建**（Docker + MySQL 8.0）
2. ✅ **30 张数仓表 DDL**（ODS 9 + DWD 7 + DWS 2 + ADS 7 + 维度 5）
3. ✅ **ETL 流程框架**（Python 实现四层加工）
4. ✅ **数据分区策略**（dt 字段支持 T+1 增量）
5. ✅ **索引优化**（每个表 3-5 个索引）
6. ✅ **权限控制设计**（行级权限 + 数据库用户）

**下一步：** 完善 ETL 逻辑 + 数据迁移 + 报表开发

---

**实施完成时间：** 2026-03-18 12:40  
**实施状态：** ✅ 框架已完成，待完善 ETL 逻辑
