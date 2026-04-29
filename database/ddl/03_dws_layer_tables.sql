-- ============================================================
-- DWS 层（服务数据层）数据表设计
-- 依据：论文 4.2.3 节 数据仓库分层表结构设计
-- 说明：DWS 层是面向分析主题的数据层，以业务主题为核心进行数据聚合
--       通过事实表与维度表的组合，形成面向特定主题的分析模型
-- ============================================================

-- 创建 DWS 数据库
CREATE DATABASE IF NOT EXISTS erp_dws DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE erp_dws;

-- ============================================================
-- DWS 层事实表 (2 张)
-- ============================================================

-- 1. Dws_sales_payment_fact 销售 - 回款事实表
-- 聚合合同销售与回款，形成销售进度分析模型
DROP TABLE IF EXISTS Dws_sales_payment_fact;
CREATE TABLE Dws_sales_payment_fact (
    FactKey VARCHAR(64) PRIMARY KEY COMMENT '事实主键（代理键）',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    RoomGUID VARCHAR(64) COMMENT '房间 GUID',
    RoomNo NVARCHAR(50) COMMENT '房间号',
    TradeGUID VARCHAR(64) COMMENT '交易 GUID',
    ContractGUID VARCHAR(64) COMMENT '合同 GUID',
    DimDateKey INT COMMENT '日期维度键（YYYYMMDD）',
    DimProjectKey INT COMMENT '项目维度键',
    DimRoomTypeKey INT COMMENT '房型维度键',
    DimBuildingKey INT COMMENT '楼栋维度键',
    -- 销售指标
    ContractAmount DECIMAL(14,2) DEFAULT 0.00 COMMENT '合同金额',
    ContractCount INT DEFAULT 0 COMMENT '合同数量',
    SignedDate DATETIME COMMENT '签约日期',
    -- 回款指标
    PaymentAmount DECIMAL(14,2) DEFAULT 0.00 COMMENT '回款金额',
    PaymentCount INT DEFAULT 0 COMMENT '回款笔数',
    UnpaidAmount DECIMAL(14,2) DEFAULT 0.00 COMMENT '未回款金额',
    PaymentRate DECIMAL(8,4) DEFAULT 0.0000 COMMENT '回款率',
    -- 衍生指标
    OverdueAmount DECIMAL(14,2) DEFAULT 0.00 COMMENT '逾期金额',
    OverdueDays INT DEFAULT 0 COMMENT '逾期天数',
    -- 时间戳
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    UpdateTime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_project (ProjectGUID),
    INDEX idx_date (DimDateKey),
    INDEX idx_contract (ContractGUID),
    INDEX idx_load_time (LoadTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 层 - 销售 - 回款事实表';

-- 2. Dws_cost_expense_fact 成本 - 费用事实表
-- 聚合合同付款及营销财务管理费用，形成成本费用分析模型
DROP TABLE IF EXISTS Dws_cost_expense_fact;
CREATE TABLE Dws_cost_expense_fact (
    FactKey VARCHAR(64) PRIMARY KEY COMMENT '事实主键（代理键）',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    ContractGUID VARCHAR(64) COMMENT '合同 GUID',
    AccountGUID VARCHAR(64) COMMENT '科目 GUID',
    DimDateKey INT COMMENT '日期维度键（YYYYMMDD）',
    DimProjectKey INT COMMENT '项目维度键',
    DimAccountKey INT COMMENT '科目维度键',
    DimCostCenterKey INT COMMENT '成本中心维度键',
    -- 合同维度
    ContractType NVARCHAR(50) COMMENT '合同类型',
    ContractName NVARCHAR(200) COMMENT '合同名称',
    PartyB NVARCHAR(100) COMMENT '乙方',
    -- 成本指标
    ContractAmount DECIMAL(14,2) DEFAULT 0.00 COMMENT '合同金额',
    PaidAmount DECIMAL(14,2) DEFAULT 0.00 COMMENT '已付金额',
    UnpaidAmount DECIMAL(14,2) DEFAULT 0.00 COMMENT '未付金额',
    -- 预算指标
    BudgetAmount DECIMAL(14,2) DEFAULT 0.00 COMMENT '预算金额',
    BudgetVariance DECIMAL(14,2) DEFAULT 0.00 COMMENT '预算偏差',
    BudgetVarianceRate DECIMAL(8,4) DEFAULT 0.0000 COMMENT '预算偏差率',
    -- 费用指标
    ExpenseAmount DECIMAL(14,2) DEFAULT 0.00 COMMENT '费用金额',
    ExpenseType NVARCHAR(50) COMMENT '费用类型',
    -- 时间戳
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    UpdateTime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_project (ProjectGUID),
    INDEX idx_date (DimDateKey),
    INDEX idx_account (AccountGUID),
    INDEX idx_contract (ContractGUID),
    INDEX idx_load_time (LoadTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 层 - 成本 - 费用事实表';

-- ============================================================
-- DWS 层维度表 (3 张)
-- ============================================================

-- 3. Dim_project 项目维度表
-- 项目信息（包含区域、产品业态、楼栋）
DROP TABLE IF EXISTS Dim_project;
CREATE TABLE Dim_project (
    ProjectKey INT AUTO_INCREMENT PRIMARY KEY COMMENT '项目维度主键（代理键）',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID（业务键）',
    ProjectCode NVARCHAR(50) COMMENT '项目编码',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    CityGUID VARCHAR(64) COMMENT '城市 GUID',
    CityName NVARCHAR(50) COMMENT '城市名称',
    RegionGUID VARCHAR(64) COMMENT '区域公司 GUID',
    RegionName NVARCHAR(100) COMMENT '区域公司名称',
    GroupFlag TINYINT DEFAULT 0 COMMENT '是否集团直管（0:否 1:是）',
    ProductType NVARCHAR(50) COMMENT '产品业态',
    BuildingNo NVARCHAR(50) COMMENT '楼栋号',
    BuildingName NVARCHAR(128) COMMENT '楼栋名称',
    TotalArea DECIMAL(14,2) COMMENT '总建筑面积',
    TotalUnits INT COMMENT '总户数',
    ProjectStatus NVARCHAR(20) COMMENT '项目状态',
    StartDate DATETIME COMMENT '开工日期',
    EndDate DATETIME COMMENT '竣工日期',
    IsCurrent TINYINT DEFAULT 1 COMMENT '是否当前版本',
    EffectiveDate DATETIME COMMENT '生效日期',
    ExpiryDate DATETIME COMMENT '失效日期',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_project_guid (ProjectGUID),
    INDEX idx_region (RegionGUID),
    INDEX idx_city (CityGUID),
    INDEX idx_is_current (IsCurrent)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 层 - 项目维度表';

-- 4. Dim_date 时间维度表
-- 年、月、日分层时间信息
DROP TABLE IF EXISTS Dim_date;
CREATE TABLE Dim_date (
    DateKey INT PRIMARY KEY COMMENT '日期键（YYYYMMDD）',
    FullDate DATE NOT NULL COMMENT '完整日期',
    Year INT COMMENT '年',
    Quarter INT COMMENT '季度',
    Month INT COMMENT '月',
    Day INT COMMENT '日',
    DayOfWeek INT COMMENT '星期几（0-6）',
    DayName NVARCHAR(10) COMMENT '星期名称',
    WeekOfYear INT COMMENT '年度第几周',
    MonthName NVARCHAR(10) COMMENT '月份名称',
    IsWeekend TINYINT DEFAULT 0 COMMENT '是否周末',
    IsHoliday TINYINT DEFAULT 0 COMMENT '是否节假日',
    HolidayName NVARCHAR(50) COMMENT '节假日名称',
    IsWorkday TINYINT DEFAULT 1 COMMENT '是否工作日',
    FiscalYear INT COMMENT '财务年度',
    FiscalQuarter INT COMMENT '财务季度',
    FiscalMonth INT COMMENT '财务月份',
    YearMonth INT COMMENT '年月（YYYYMM）',
    YearQuarter VARCHAR(7) COMMENT '年季（YYYYQn）',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_full_date (FullDate),
    INDEX idx_year (Year),
    INDEX idx_month (YearMonth),
    INDEX idx_fiscal_year (FiscalYear)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 层 - 时间维度表';

-- 5. Dim_account 科目维度表
-- 财务科目信息
DROP TABLE IF EXISTS Dim_account;
CREATE TABLE Dim_account (
    AccountKey INT AUTO_INCREMENT PRIMARY KEY COMMENT '科目维度主键（代理键）',
    AccountGUID VARCHAR(64) COMMENT '科目 GUID（业务键）',
    AccountCode NVARCHAR(50) COMMENT '科目编码',
    AccountName NVARCHAR(100) COMMENT '科目名称',
    AccountType NVARCHAR(50) COMMENT '科目类型',
    ParentGUID VARCHAR(64) COMMENT '上级科目 GUID',
    ParentKey INT COMMENT '上级科目维度键',
    Level INT COMMENT '科目级次',
    IsLeaf TINYINT DEFAULT 0 COMMENT '是否末级科目',
    AccountCategory NVARCHAR(50) COMMENT '科目类别（资产/负债/权益/成本/损益）',
    AccountDirection NVARCHAR(10) COMMENT '余额方向（借/贷）',
    IsCashFlow TINYINT DEFAULT 0 COMMENT '是否现金流量科目',
    AccountStatus NVARCHAR(20) COMMENT '科目状态',
    IsCurrent TINYINT DEFAULT 1 COMMENT '是否当前版本',
    EffectiveDate DATETIME COMMENT '生效日期',
    ExpiryDate DATETIME COMMENT '失效日期',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_account_guid (AccountGUID),
    INDEX idx_account_code (AccountCode),
    INDEX idx_parent_key (ParentKey),
    INDEX idx_is_current (IsCurrent)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 层 - 科目维度表';

-- ============================================================
-- 初始化时间维度表数据（2020-2030 年）
-- ============================================================

-- 存储过程：生成时间维度数据
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS sp_init_dim_date()
BEGIN
    DECLARE start_date DATE DEFAULT '2020-01-01';
    DECLARE end_date DATE DEFAULT '2030-12-31';
    DECLARE current_date_val DATE DEFAULT start_date;
    DECLARE date_key_val INT;
    DECLARE year_val, quarter_val, month_val, day_val, dow_val, week_val INT;
    DECLARE day_name_val, month_name_val VARCHAR(10);
    DECLARE is_weekend_val, is_workday_val INT;
    DECLARE fiscal_year_val, fiscal_month_val INT;
    DECLARE year_month_val INT;

    WHILE current_date_val <= end_date DO
        SET date_key_val = YEAR(current_date_val) * 10000 + MONTH(current_date_val) * 100 + DAY(current_date_val);
        SET year_val = YEAR(current_date_val);
        SET quarter_val = QUARTER(current_date_val);
        SET month_val = MONTH(current_date_val);
        SET day_val = DAY(current_date_val);
        SET dow_val = WEEKDAY(current_date_val);
        SET week_val = WEEK(current_date_val, 1);

        CASE dow_val
            WHEN 0 THEN SET day_name_val = 'Monday';
            WHEN 1 THEN SET day_name_val = 'Tuesday';
            WHEN 2 THEN SET day_name_val = 'Wednesday';
            WHEN 3 THEN SET day_name_val = 'Thursday';
            WHEN 4 THEN SET day_name_val = 'Friday';
            WHEN 5 THEN SET day_name_val = 'Saturday';
            WHEN 6 THEN SET day_name_val = 'Sunday';
        END CASE;

        CASE month_val
            WHEN 1 THEN SET month_name_val = 'January';
            WHEN 2 THEN SET month_name_val = 'February';
            WHEN 3 THEN SET month_name_val = 'March';
            WHEN 4 THEN SET month_name_val = 'April';
            WHEN 5 THEN SET month_name_val = 'May';
            WHEN 6 THEN SET month_name_val = 'June';
            WHEN 7 THEN SET month_name_val = 'July';
            WHEN 8 THEN SET month_name_val = 'August';
            WHEN 9 THEN SET month_name_val = 'September';
            WHEN 10 THEN SET month_name_val = 'October';
            WHEN 11 THEN SET month_name_val = 'November';
            WHEN 12 THEN SET month_name_val = 'December';
        END CASE;

        SET is_weekend_val = IF(dow_val >= 5, 1, 0);
        SET is_workday_val = 1 - is_weekend_val;

        SET fiscal_year_val = year_val;
        SET fiscal_month_val = month_val;
        SET year_month_val = year_val * 100 + month_val;

        INSERT INTO Dim_date (
            DateKey, FullDate, Year, Quarter, Month, Day, DayOfWeek, DayName,
            WeekOfYear, MonthName, IsWeekend, IsWorkday,
            FiscalYear, FiscalMonth, YearMonth
        ) VALUES (
            date_key_val, current_date_val, year_val, quarter_val, month_val, day_val,
            dow_val, day_name_val, week_val, month_name_val,
            is_weekend_val, is_workday_val,
            fiscal_year_val, fiscal_month_val, year_month_val
        )
        ON DUPLICATE KEY UPDATE FullDate = VALUES(FullDate);

        SET current_date_val = DATE_ADD(current_date_val, INTERVAL 1 DAY);
    END WHILE;
END$$
DELIMITER ;
