-- ============================================================
-- ADS 层（应用数据层）数据表设计
-- 依据：论文 4.2.3 节 数据仓库分层表结构设计
-- 说明：ADS 层是最接近业务端的一层，直接服务于报表、数据分析和管理驾驶舱
--       该层根据具体报表定义，将 DWS 的主题数据进行二次聚合和指标计算
-- ============================================================

-- 创建 ADS 数据库
CREATE DATABASE IF NOT EXISTS erp_ads DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE erp_ads;

-- ============================================================
-- ADS 层报表数据表 (7 张)
-- ============================================================

-- 1. Ads_group_sales_report 集团销售目标达成表
-- 支撑集团层级的销售进度分析
DROP TABLE IF EXISTS Ads_group_sales_report;
CREATE TABLE Ads_group_sales_report (
    ReportKey VARCHAR(64) PRIMARY KEY COMMENT '报表主键',
    RegionGUID VARCHAR(64) COMMENT '区域公司 GUID',
    RegionName NVARCHAR(100) COMMENT '区域公司名称',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    StatYear INT COMMENT '统计年度',
    StatMonth INT COMMENT '统计月份',
    StatDate DATE COMMENT '统计日期',
    -- 目标指标
    SalesTargetAmount DECIMAL(16,2) DEFAULT 0.00 COMMENT '销售目标金额',
    SalesTargetArea DECIMAL(14,2) DEFAULT 0.00 COMMENT '销售目标面积',
    SalesTargetUnits INT DEFAULT 0 COMMENT '销售目标套数',
    -- 实际指标
    ActualSalesAmount DECIMAL(16,2) DEFAULT 0.00 COMMENT '实际销售金额',
    ActualSalesArea DECIMAL(14,2) DEFAULT 0.00 COMMENT '实际销售面积',
    ActualSalesUnits INT DEFAULT 0 COMMENT '实际销售套数',
    -- 达成率
    SalesAmountRate DECIMAL(8,4) DEFAULT 0.0000 COMMENT '销售金额达成率',
    SalesAreaRate DECIMAL(8,4) DEFAULT 0.0000 COMMENT '销售面积达成率',
    SalesUnitsRate DECIMAL(8,4) DEFAULT 0.0000 COMMENT '销售套数达成率',
    -- 排名
    RegionRank INT COMMENT '区域排名',
    ProjectRank INT COMMENT '项目排名',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_region (RegionGUID),
    INDEX idx_project (ProjectGUID),
    INDEX idx_stat_date (StatDate),
    INDEX idx_year_month (StatYear, StatMonth)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 集团销售目标达成表';

-- 2. Ads_group_salesdate_report 集团签约回款周月年报
-- 支撑集团层级的销售周报月报年报
DROP TABLE IF EXISTS Ads_group_salesdate_report;
CREATE TABLE Ads_group_salesdate_report (
    ReportKey VARCHAR(64) PRIMARY KEY COMMENT '报表主键',
    ReportType VARCHAR(20) COMMENT '报表类型：daily/weekly/monthly/yearly',
    RegionGUID VARCHAR(64) COMMENT '区域公司 GUID',
    RegionName NVARCHAR(100) COMMENT '区域公司名称',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    StartDate DATE COMMENT '统计开始日期',
    EndDate DATE COMMENT '统计结束日期',
    -- 认购指标
    SubCount INT DEFAULT 0 COMMENT '认购套数',
    SubAmount DECIMAL(16,2) DEFAULT 0.00 COMMENT '认购金额',
    SubArea DECIMAL(14,2) DEFAULT 0.00 COMMENT '认购面积',
    SubAvgPrice DECIMAL(12,2) DEFAULT 0.00 COMMENT '认购均价',
    -- 签约指标
    SignCount INT DEFAULT 0 COMMENT '签约套数',
    SignAmount DECIMAL(16,2) DEFAULT 0.00 COMMENT '签约金额',
    SignArea DECIMAL(14,2) DEFAULT 0.00 COMMENT '签约面积',
    SignAvgPrice DECIMAL(12,2) DEFAULT 0.00 COMMENT '签约均价',
    -- 回款指标
    PaymentCount INT DEFAULT 0 COMMENT '回款笔数',
    PaymentAmount DECIMAL(16,2) DEFAULT 0.00 COMMENT '回款金额',
    -- 比率指标
    SignSubRate DECIMAL(8,4) DEFAULT 0.0000 COMMENT '签约认购比',
    PaymentSignRate DECIMAL(8,4) DEFAULT 0.0000 COMMENT '回款签约比',
    -- 环比同比
    AmountWoW DECIMAL(8,4) DEFAULT 0.0000 COMMENT '金额环比',
    AmountYoY DECIMAL(8,4) DEFAULT 0.0000 COMMENT '金额同比',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_report_type (ReportType),
    INDEX idx_region (RegionGUID),
    INDEX idx_project (ProjectGUID),
    INDEX idx_date_range (StartDate, EndDate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 集团签约回款周月年报';

-- 3. Ads_group_pay_report 集团费用支出汇总表
-- 支撑高层决策，包含合同支出及三费支出
DROP TABLE IF EXISTS Ads_group_pay_report;
CREATE TABLE Ads_group_pay_report (
    ReportKey VARCHAR(64) PRIMARY COMMENT '报表主键',
    RegionGUID VARCHAR(64) COMMENT '区域公司 GUID',
    RegionName NVARCHAR(100) COMMENT '区域公司名称',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    StatYear INT COMMENT '统计年度',
    StatMonth INT COMMENT '统计月份',
    StatDate DATE COMMENT '统计日期',
    -- 合同支出
    ContractPayAmount DECIMAL(16,2) DEFAULT 0.00 COMMENT '合同付款金额',
    ContractCount INT DEFAULT 0 COMMENT '合同付款笔数',
    NoContractPayAmount DECIMAL(16,2) DEFAULT 0.00 COMMENT '无合同付款金额',
    -- 三费支出
    ManagementFee DECIMAL(16,2) DEFAULT 0.00 COMMENT '管理费用',
    SalesFee DECIMAL(16,2) DEFAULT 0.00 COMMENT '销售费用',
    FinancialFee DECIMAL(16,2) DEFAULT 0.00 COMMENT '财务费用',
    TotalExpense DECIMAL(16,2) DEFAULT 0.00 COMMENT '费用合计',
    -- 预算对比
    ExpenseBudget DECIMAL(16,2) DEFAULT 0.00 COMMENT '费用预算',
    ExpenseVariance DECIMAL(16,2) DEFAULT 0.00 COMMENT '费用偏差',
    ExpenseVarianceRate DECIMAL(8,4) DEFAULT 0.0000 COMMENT '费用偏差率',
    -- 占比
    PayTotalRatio DECIMAL(8,4) DEFAULT 0.0000 COMMENT '付款占总支出比例',
    ExpenseTotalRatio DECIMAL(8,4) DEFAULT 0.0000 COMMENT '费用占总支出比例',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_region (RegionGUID),
    INDEX idx_project (ProjectGUID),
    INDEX idx_stat_date (StatDate),
    INDEX idx_year_month (StatYear, StatMonth)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 集团费用支出汇总表';

-- 4. Ads_project_cost_report 项目成本费用报表
-- 支撑项目维度的成本控制分析
DROP TABLE IF EXISTS Ads_project_cost_report;
CREATE TABLE Ads_project_cost_report (
    ReportKey VARCHAR(64) PRIMARY COMMENT '报表主键',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    StatYear INT COMMENT '统计年度',
    StatMonth INT COMMENT '统计月份',
    StatDate DATE COMMENT '统计日期',
    -- 土地成本
    LandCost DECIMAL(16,2) DEFAULT 0.00 COMMENT '土地成本',
    LandArea DECIMAL(14,2) DEFAULT 0.00 COMMENT '土地面积',
    LandUnitPrice DECIMAL(12,2) DEFAULT 0.00 COMMENT '土地楼面价',
    -- 建安成本
    ConstructionCost DECIMAL(16,2) DEFAULT 0.00 COMMENT '建安成本',
    InstallationCost DECIMAL(16,2) DEFAULT 0.00 COMMENT '安装成本',
    DecorationCost DECIMAL(16,2) DEFAULT 0.00 COMMENT '装修成本',
    -- 配套成本
    FacilityCost DECIMAL(16,2) DEFAULT 0.00 COMMENT '配套设施成本',
    InfrastructureCost DECIMAL(16,2) DEFAULT 0.00 COMMENT '基础设施成本',
    -- 开发间接费
    DevIndirectCost DECIMAL(16,2) DEFAULT 0.00 COMMENT '开发间接费',
    -- 总成本
    TotalCost DECIMAL(16,2) DEFAULT 0.00 COMMENT '总成本',
    TotalArea DECIMAL(14,2) DEFAULT 0.00 COMMENT '总建筑面积',
    UnitCost DECIMAL(12,2) DEFAULT 0.00 COMMENT '单位成本',
    -- 预算对比
    CostBudget DECIMAL(16,2) DEFAULT 0.00 COMMENT '成本预算',
    CostVariance DECIMAL(16,2) DEFAULT 0.00 COMMENT '成本偏差',
    CostVarianceRate DECIMAL(8,4) DEFAULT 0.0000 COMMENT '成本偏差率',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_project (ProjectGUID),
    INDEX idx_stat_date (StatDate),
    INDEX idx_year_month (StatYear, StatMonth)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 项目成本费用报表';

-- 5. Ads_sales_dashboard 营销驾驶舱大屏
-- 支撑高层管理驾驶舱可视化展示
DROP TABLE IF EXISTS Ads_sales_dashboard;
CREATE TABLE Ads_sales_dashboard (
    RecordKey VARCHAR(64) PRIMARY COMMENT '记录主键',
    DataType VARCHAR(50) COMMENT '数据类型',
    RegionGUID VARCHAR(64) COMMENT '区域公司 GUID',
    RegionName NVARCHAR(100) COMMENT '区域公司名称',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    StatDate DATE COMMENT '统计日期',
    StatTime DATETIME COMMENT '统计时间点',
    -- 核心指标
    MetricName NVARCHAR(100) COMMENT '指标名称',
    MetricValue DECIMAL(16,4) COMMENT '指标值',
    MetricUnit NVARCHAR(20) COMMENT '指标单位',
    TargetValue DECIMAL(16,4) DEFAULT 0.00 COMMENT '目标值',
    AchievementRate DECIMAL(8,4) DEFAULT 0.0000 COMMENT '达成率',
    -- 趋势指标
    WoW DECIMAL(8,4) DEFAULT 0.0000 COMMENT '环比',
    YoY DECIMAL(8,4) DEFAULT 0.0000 COMMENT '同比',
    -- 预警
    WarningLevel VARCHAR(10) DEFAULT 'normal' COMMENT '预警级别：normal/warning/critical',
    DisplayOrder INT DEFAULT 0 COMMENT '显示顺序',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_data_type (DataType),
    INDEX idx_region (RegionGUID),
    INDEX idx_project (ProjectGUID),
    INDEX idx_stat_date (StatDate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 营销驾驶舱大屏数据表';

-- 6. Ads_finance_dashboard 财务驾驶舱大屏
-- 支撑高层管理驾驶舱可视化展示
DROP TABLE IF EXISTS Ads_finance_dashboard;
CREATE TABLE Ads_finance_dashboard (
    RecordKey VARCHAR(64) PRIMARY COMMENT '记录主键',
    DataType VARCHAR(50) COMMENT '数据类型',
    RegionGUID VARCHAR(64) COMMENT '区域公司 GUID',
    RegionName NVARCHAR(100) COMMENT '区域公司名称',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    StatDate DATE COMMENT '统计日期',
    StatTime DATETIME COMMENT '统计时间点',
    -- 核心指标
    MetricName NVARCHAR(100) COMMENT '指标名称',
    MetricValue DECIMAL(16,4) COMMENT '指标值',
    MetricUnit NVARCHAR(20) COMMENT '指标单位',
    TargetValue DECIMAL(16,4) DEFAULT 0.00 COMMENT '目标值',
    AchievementRate DECIMAL(8,4) DEFAULT 0.0000 COMMENT '达成率',
    -- 趋势指标
    WoW DECIMAL(8,4) DEFAULT 0.0000 COMMENT '环比',
    YoY DECIMAL(8,4) DEFAULT 0.0000 COMMENT '同比',
    -- 预警
    WarningLevel VARCHAR(10) DEFAULT 'normal' COMMENT '预警级别：normal/warning/critical',
    DisplayOrder INT DEFAULT 0 COMMENT '显示顺序',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_data_type (DataType),
    INDEX idx_region (RegionGUID),
    INDEX idx_project (ProjectGUID),
    INDEX idx_stat_date (StatDate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 财务驾驶舱大屏数据表';

-- 7. Ads_szl_dashboard 收支利大屏
-- 结合销售成本费用，综合分析大屏
DROP TABLE IF EXISTS Ads_szl_dashboard;
CREATE TABLE Ads_szl_dashboard (
    RecordKey VARCHAR(64) PRIMARY COMMENT '记录主键',
    RegionGUID VARCHAR(64) COMMENT '区域公司 GUID',
    RegionName NVARCHAR(100) COMMENT '区域公司名称',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    StatYear INT COMMENT '统计年度',
    StatMonth INT COMMENT '统计月份',
    StatDate DATE COMMENT '统计日期',
    -- 收入类
    SalesRevenue DECIMAL(16,2) DEFAULT 0.00 COMMENT '销售收入',
    OtherRevenue DECIMAL(16,2) DEFAULT 0.00 COMMENT '其他收入',
    TotalRevenue DECIMAL(16,2) DEFAULT 0.00 COMMENT '收入合计',
    -- 支出类
    LandExpense DECIMAL(16,2) DEFAULT 0.00 COMMENT '土地支出',
    ConstructionExpense DECIMAL(16,2) DEFAULT 0.00 COMMENT '建安支出',
    FacilityExpense DECIMAL(16,2) DEFAULT 0.00 COMMENT '配套支出',
    TaxExpense DECIMAL(16,2) DEFAULT 0.00 COMMENT '税金支出',
    ExpenseTotal DECIMAL(16,2) DEFAULT 0.00 COMMENT '费用合计',
    TotalExpense DECIMAL(16,2) DEFAULT 0.00 COMMENT '支出合计',
    -- 利润类
    GrossProfit DECIMAL(16,2) DEFAULT 0.00 COMMENT '毛利润',
    OperatingProfit DECIMAL(16,2) DEFAULT 0.00 COMMENT '营业利润',
    NetProfit DECIMAL(16,2) DEFAULT 0.00 COMMENT '净利润',
    -- 利润率
    GrossMargin DECIMAL(8,4) DEFAULT 0.0000 COMMENT '毛利率',
    OperatingMargin DECIMAL(8,4) DEFAULT 0.0000 COMMENT '营业利润率',
    NetMargin DECIMAL(8,4) DEFAULT 0.0000 COMMENT '净利率',
    -- 现金流
    CashInflow DECIMAL(16,2) DEFAULT 0.00 COMMENT '现金流入',
    CashOutflow DECIMAL(16,2) DEFAULT 0.00 COMMENT '现金流出',
    NetCashFlow DECIMAL(16,2) DEFAULT 0.00 COMMENT '净现金流',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_region (RegionGUID),
    INDEX idx_project (ProjectGUID),
    INDEX idx_stat_date (StatDate),
    INDEX idx_year_month (StatYear, StatMonth)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 收支利大屏数据表';

-- ============================================================
-- RPA 巡检相关表
-- ============================================================

-- RPA 巡检规则表
DROP TABLE IF EXISTS rpa_inspect_rule;
CREATE TABLE rpa_inspect_rule (
    RuleID INT AUTO_INCREMENT PRIMARY KEY COMMENT '规则 ID',
    RuleName NVARCHAR(100) COMMENT '规则名称',
    RuleSQL TEXT COMMENT '巡检规则 SQL',
    Severity VARCHAR(20) DEFAULT 'medium' COMMENT '严重等级：low/medium/high/critical',
    PushChannel VARCHAR(50) DEFAULT 'system' COMMENT '推送渠道：system/dingtalk/email',
    IsActive TINYINT DEFAULT 1 COMMENT '是否启用',
    CreatedTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UpdatedTime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_is_active (IsActive),
    INDEX idx_severity (Severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RPA 巡检规则表';

-- RPA 巡检日志表
DROP TABLE IF EXISTS rpa_inspection_log;
CREATE TABLE rpa_inspection_log (
    LogID BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '日志 ID',
    RuleID INT COMMENT '规则 ID',
    RuleName NVARCHAR(100) COMMENT '规则名称',
    ExceptionCount INT DEFAULT 0 COMMENT '异常数量',
    ExceptionData TEXT COMMENT '异常数据 JSON',
    PushStatus VARCHAR(20) DEFAULT 'pending' COMMENT '推送状态：pending/sent/failed',
    PushTime DATETIME COMMENT '推送时间',
    ProcessedBy VARCHAR(64) COMMENT '处理人 GUID',
    ProcessedTime DATETIME COMMENT '处理时间',
    ProcessResult NVARCHAR(500) COMMENT '处理结果',
    Status VARCHAR(20) DEFAULT 'open' COMMENT '状态：open/processing/closed',
    CreatedTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_rule_id (RuleID),
    INDEX idx_status (Status),
    INDEX idx_created_time (CreatedTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RPA 巡检日志表';
