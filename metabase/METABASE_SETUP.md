# Metabase BI 报表配置指南

## 📊 数据源配置

### 1. 连接 MySQL 数仓

1. 访问 http://localhost:3001
2. 首次启动需要设置管理员账号
3. 添加数据源：
   - **数据库类型**: MySQL
   - **主机**: erp-bi-mysql (Docker 网络) 或 localhost (本机)
   - **端口**: 3306
   - **数据库名**: erp_bi_warehouse
   - **用户名**: erp_bi
   - **密码**: erp_bi123

### 2. 推荐的数据表同步顺序

1. **ODS 层** - 原始数据（可选同步）
2. **DWD 层** - 清洗后的明细数据（推荐）
3. **DWS 层** - 聚合事实表（核心）
4. **ADS 层** - 报表数据（直接用于仪表板）

---

## 📈 推荐创建的仪表板

### 1. 营销驾驶舱

**数据源**: `ads_sales_dashboard`

**指标卡片**:
- 总房源数
- 已售房源数
- 可售房源数
- 去化率 (%)
- 总销售额
- 平均单价

**图表**:
- 项目去化率对比（柱状图）
- 房源状态分布（饼图）
- 销售趋势（折线图）

**SQL 查询示例**:
```sql
SELECT 
    project_name,
    total_units,
    sold_units,
    available_units,
    sell_through_rate,
    total_sales
FROM ads_sales_dashboard
WHERE dt = CURDATE()
ORDER BY total_sales DESC
```

---

### 2. 销售 - 回款分析

**数据源**: `dws_sales_payment_fact`

**指标卡片**:
- 合同总数
- 回款总数
- 合同金额
- 回款金额
- 回款率 (%)

**图表**:
- 月度销售趋势（折线图）
- 回款率趋势（折线图）
- 项目销售对比（柱状图）

**SQL 查询示例**:
```sql
SELECT 
    YEAR(date_key) as year,
    MONTH(date_key) as month,
    SUM(contract_amount) as contract_amount,
    SUM(payment_amount) as payment_amount,
    AVG(payment_rate) as payment_rate
FROM dws_sales_payment_fact
WHERE dt = CURDATE()
GROUP BY YEAR(date_key), MONTH(date_key)
ORDER BY year, month
```

---

### 3. 房源明细查询

**数据源**: `dwd_room_detail`

**筛选条件**:
- 项目
- 楼栋
- 房型
- 状态（可售/已签约/已交付）
- 价格区间

**展示字段**:
- 房号
- 楼层
- 建筑面积
- 总价
- 单价
- 状态

**SQL 查询示例**:
```sql
SELECT 
    room_code,
    room_name,
    floor,
    room_type,
    building_area,
    total_price,
    unit_price,
    room_status
FROM dwd_room_detail
WHERE dt = CURDATE()
ORDER BY room_code
LIMIT 100
```

---

### 4. 财务驾驶舱

**数据源**: `ads_finance_dashboard`（待完善）

**指标卡片**:
- 总收入
- 总成本
- 利润率
- 预算执行率

---

## 🔧 Metabase 配置技巧

### 1. 创建计算字段

在 Metabase 中可以创建计算字段：

```
回款率 = payment_amount / contract_amount * 100
去化率 = sold_units / total_units * 100
```

### 2. 设置数据刷新

- **ODS/DWD 层**: 每小时刷新
- **DWS/ADS 层**: 每天刷新（ETL 完成后）

### 3. 权限配置

- **管理员**: 所有表可读写
- **分析师**: DWS/ADS层只读
- **业务用户**: ADS 层只读（特定项目）

---

## 📋 仪表板布局建议

### 首页（管理驾驶舱）
```
┌─────────────────────────────────────────────────────┐
│  [总房源]  [已售]  [去化率]  [销售额]  [回款率]    │
├─────────────────────────────────────────────────────┤
│                                                     │
│   [项目去化率对比柱状图]    [房源状态分布饼图]      │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│   [销售趋势折线图]          [Top10 房源列表]        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 销售分析页
```
┌─────────────────────────────────────────────────────┐
│  [合同数]  [合同金额]  [回款数]  [回款金额]        │
├─────────────────────────────────────────────────────┤
│                                                     │
│   [月度销售趋势]          [项目销售对比]            │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│   [销售明细表格]（支持筛选和导出）                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

1. **启动 Metabase**: `docker ps | grep metabase`
2. **访问**: http://localhost:3001
3. **设置管理员**: 邮箱 + 密码
4. **添加数据源**: MySQL → erp_bi_warehouse
5. **同步表结构**: 选择 DWS/ADS 层表
6. **创建第一个仪表板**: 选择 ads_sales_dashboard

---

**文档更新时间**: 2026-03-19
