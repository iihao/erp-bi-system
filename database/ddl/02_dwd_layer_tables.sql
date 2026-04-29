-- ============================================================
-- DWD 层（明细数据层）数据表设计
-- 依据：论文 4.2.3 节 数据仓库分层表结构设计
-- 说明：DWD 层是在 ODS 基础上的标准化与清洗层
--       目标是统一口径、去除冗余和无效信息，形成高质量的明细数据
-- ============================================================

-- 创建 DWD 数据库
CREATE DATABASE IF NOT EXISTS erp_dwd DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE erp_dwd;

-- ============================================================
-- DWD 层明细表 (7 张)
-- ============================================================

-- 1. Dwd_room_detail 房源明细表
-- 清洗后的房源数据，用于计算项目货值
DROP TABLE IF EXISTS Dwd_room_detail;
CREATE TABLE Dwd_room_detail (
    RoomKey VARCHAR(64) PRIMARY KEY COMMENT '房间主键（代理键）',
    RoomGUID VARCHAR(64) NOT NULL COMMENT '房间 GUID（业务键）',
    RoomNo NVARCHAR(50) COMMENT '房间号',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    BuildingNo NVARCHAR(50) COMMENT '楼栋号',
    BuildingName NVARCHAR(128) COMMENT '楼栋名称',
    UnitNo NVARCHAR(50) COMMENT '单元号',
    FloorNo INT COMMENT '楼层号',
    Area DECIMAL(12,2) COMMENT '建筑面积',
    InnerArea DECIMAL(12,2) COMMENT '套内面积',
    PublicArea DECIMAL(12,2) COMMENT '公摊面积',
    RoomType NVARCHAR(50) COMMENT '房型',
    RoomStatus NVARCHAR(50) COMMENT '房间状态（标准化）',
    Price DECIMAL(14,2) COMMENT '房屋总价',
    UnitPrice DECIMAL(12,2) COMMENT '单价',
    Orientation NVARCHAR(20) COMMENT '朝向',
    DataStatus VARCHAR(20) DEFAULT 'valid' COMMENT '数据状态：valid/invalid/pending',
    ExtractTime DATETIME COMMENT '原始数据抽取时间',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_project (ProjectGUID),
    INDEX idx_status (RoomStatus),
    INDEX idx_load_time (LoadTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 房源明细表';

-- 2. Dwd_trade_detail 销售明细表
-- 清洗后的房源认购签约数据，去除无效数据
DROP TABLE IF EXISTS Dwd_trade_detail;
CREATE TABLE Dwd_trade_detail (
    TradeKey VARCHAR(64) PRIMARY KEY COMMENT '交易主键（代理键）',
    TradeGUID VARCHAR(64) NOT NULL COMMENT '交易 GUID（业务键）',
    CompanyGUID VARCHAR(64) COMMENT '公司 GUID',
    BuyerAllCardIds NVARCHAR(1024) COMMENT '所有买方证件号码',
    BuyerAllNames NVARCHAR(1024) COMMENT '所有买方姓名',
    CloseReason NVARCHAR(128) COMMENT '关闭原因',
    ContractGUID VARCHAR(64) COMMENT '最后合同 GUID',
    ContractSignDate DATETIME COMMENT '最后合同签署日期（标准化）',
    ContractBizDate DATETIME COMMENT '最后合同业务归属日期（标准化）',
    HasDelayPay TINYINT DEFAULT 0 COMMENT '是否存在延期付款（0:否 1:是）',
    LastFollowDate DATETIME COMMENT '最近跟进日期',
    PreTradeGUID VARCHAR(64) COMMENT '前次交易 GUID',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    SubGUID VARCHAR(64) COMMENT '最后认购 GUID',
    SubDate DATETIME COMMENT '最后认购日期',
    SubType NVARCHAR(50) COMMENT '最后认购类型（标准化）',
    RoomGUID VARCHAR(64) COMMENT '房间 GUID',
    RoomStatus NVARCHAR(50) COMMENT '房间状态（标准化）',
    TradeStatus NVARCHAR(50) COMMENT '交易状态（标准化）',
    CreatorGUID VARCHAR(64) COMMENT '创建人 GUID',
    CreatorName NVARCHAR(100) COMMENT '创建人名称',
    CreateTime DATETIME COMMENT '创建时间',
    ModifierGUID VARCHAR(64) COMMENT '修改人 GUID',
    ModifierName NVARCHAR(100) COMMENT '修改人名称',
    ModifyTime DATETIME COMMENT '修改时间',
    DataStatus VARCHAR(20) DEFAULT 'valid' COMMENT '数据状态：valid/invalid/duplicate',
    ExtractTime DATETIME COMMENT '原始数据抽取时间',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_project (ProjectGUID),
    INDEX idx_room (RoomGUID),
    INDEX idx_contract (ContractGUID),
    INDEX idx_trade_status (TradeStatus),
    INDEX idx_load_time (LoadTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 销售明细表';

-- 3. Dwd_payment_detail 回款明细表
-- 清洗后的回款明细，去除无效和重复记录
DROP TABLE IF EXISTS Dwd_payment_detail;
CREATE TABLE Dwd_payment_detail (
    PaymentKey VARCHAR(64) PRIMARY KEY COMMENT '回款主键（代理键）',
    PayGUID VARCHAR(64) NOT NULL COMMENT '回款 GUID（业务键）',
    TradeGUID VARCHAR(64) COMMENT '交易 GUID',
    ContractGUID VARCHAR(64) COMMENT '合同 GUID',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    PayAmount DECIMAL(14,2) COMMENT '回款金额（标准化，保留 2 位小数）',
    PayDate DATETIME COMMENT '回款日期（标准化）',
    PayType NVARCHAR(50) COMMENT '回款类型（标准化）',
    PayWay NVARCHAR(50) COMMENT '付款方式（标准化）',
    BankName NVARCHAR(100) COMMENT '银行名称',
    LoanType NVARCHAR(50) COMMENT '贷款类型（标准化）',
    PayStatus NVARCHAR(20) COMMENT '回款状态（标准化）',
    DataStatus VARCHAR(20) DEFAULT 'valid' COMMENT '数据状态：valid/invalid/duplicate',
    ExtractTime DATETIME COMMENT '原始数据抽取时间',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_project (ProjectGUID),
    INDEX idx_trade (TradeGUID),
    INDEX idx_contract (ContractGUID),
    INDEX idx_pay_date (PayDate),
    INDEX idx_load_time (LoadTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 回款明细表';

-- 4. Dwd_contract_detail 合同明细表
-- 合同清洗后的明细数据，含合同金额、科目
DROP TABLE IF EXISTS Dwd_contract_detail;
CREATE TABLE Dwd_contract_detail (
    ContractKey VARCHAR(64) PRIMARY COMMENT '合同主键（代理键）',
    ContractGUID VARCHAR(64) NOT NULL COMMENT '合同 GUID（业务键）',
    ContractCode NVARCHAR(50) COMMENT '合同编码',
    ContractName NVARCHAR(200) COMMENT '合同名称',
    ContractType NVARCHAR(50) COMMENT '合同类型（标准化）',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    PartyA NVARCHAR(100) COMMENT '甲方',
    PartyB NVARCHAR(100) COMMENT '乙方',
    SignDate DATETIME COMMENT '签订日期（标准化）',
    StartDate DATETIME COMMENT '开始日期',
    EndDate DATETIME COMMENT '结束日期',
    ContractAmount DECIMAL(14,2) COMMENT '合同金额（标准化）',
    PaidAmount DECIMAL(14,2) COMMENT '已付金额（标准化）',
    UnpaidAmount DECIMAL(14,2) COMMENT '未付金额（标准化）',
    AccountGUID VARCHAR(64) COMMENT '科目 GUID',
    AccountCode NVARCHAR(50) COMMENT '科目编码',
    ContractStatus NVARCHAR(20) COMMENT '合同状态（标准化）',
    DataStatus VARCHAR(20) DEFAULT 'valid' COMMENT '数据状态：valid/invalid/pending',
    ExtractTime DATETIME COMMENT '原始数据抽取时间',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_project (ProjectGUID),
    INDEX idx_account (AccountGUID),
    INDEX idx_contract_type (ContractType),
    INDEX idx_load_time (LoadTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 合同明细表';

-- 5. Dwd_pay_detail 付款明细表
-- 清洗后的付款明细数据，含无合同付款
DROP TABLE IF EXISTS Dwd_pay_detail;
CREATE TABLE Dwd_pay_detail (
    PayRegKey VARCHAR(64) PRIMARY COMMENT '付款登记主键（代理键）',
    PayRegGUID VARCHAR(64) NOT NULL COMMENT '付款登记 GUID（业务键）',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ContractGUID VARCHAR(64) COMMENT '合同 GUID',
    PayRegAmount DECIMAL(14,2) COMMENT '付款金额（标准化）',
    PayRegDate DATETIME COMMENT '付款日期（标准化）',
    PayType NVARCHAR(50) COMMENT '付款类型（标准化）',
    PayeeName NVARCHAR(100) COMMENT '收款方名称',
    PayeeBank NVARCHAR(100) COMMENT '收款方银行',
    PayeeAccount NVARCHAR(50) COMMENT '收款方账号',
    InvoiceNo NVARCHAR(50) COMMENT '发票号码',
    PayStatus NVARCHAR(20) COMMENT '付款状态（标准化）',
    HasContract TINYINT DEFAULT 1 COMMENT '是否有合同关联（0:否 1:是）',
    DataStatus VARCHAR(20) DEFAULT 'valid' COMMENT '数据状态：valid/invalid/pending',
    ExtractTime DATETIME COMMENT '原始数据抽取时间',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_project (ProjectGUID),
    INDEX idx_contract (ContractGUID),
    INDEX idx_pay_date (PayRegDate),
    INDEX idx_load_time (LoadTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 付款明细表';

-- 6. Dwd_gl_actual_detail 总账实际明细表
-- SAP 总账实际业务数据的标准化版本
DROP TABLE IF EXISTS Dwd_gl_actual_detail;
CREATE TABLE Dwd_gl_actual_detail (
    GlActualKey VARCHAR(64) PRIMARY COMMENT '总账实际业务主键（代理键）',
    GlActualGUID VARCHAR(64) NOT NULL COMMENT '总账实际业务 GUID（业务键）',
    FiscalYear VARCHAR(4) COMMENT '会计年度',
    RecordType VARCHAR(1) COMMENT '记录类型（标准化）',
    Version VARCHAR(2) COMMENT '版本号',
    Ledger VARCHAR(2) COMMENT '分类账',
    Period INT COMMENT '期间',
    CostElement VARCHAR(10) COMMENT '成本要素',
    CostCenter VARCHAR(10) COMMENT '成本中心',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProfitCenter VARCHAR(10) COMMENT '利润中心',
    CurrencyType VARCHAR(1) COMMENT '货币类型',
    ActualAmountLocal DECIMAL(24,2) COMMENT '实际金额本币（标准化）',
    ActualAmountTrans DECIMAL(24,2) COMMENT '实际金额交易币（标准化）',
    ActualAmountObj DECIMAL(24,2) COMMENT '实际金额对象币（标准化）',
    TransactionCurrency VARCHAR(5) COMMENT '交易货币',
    Quantity DECIMAL(24,3) COMMENT '数量',
    Unit VARCHAR(3) COMMENT '数量单位',
    PostingDate DATETIME COMMENT '过账日期（标准化）',
    DocumentDate DATETIME COMMENT '凭证日期',
    DebitCredit VARCHAR(1) COMMENT '借贷标识（标准化）',
    DocumentStatus VARCHAR(2) COMMENT '凭证状态',
    ReferenceDoc VARCHAR(16) COMMENT '参考凭证编号',
    LineItemText NVARCHAR(50) COMMENT '行项目文本',
    DataStatus VARCHAR(20) DEFAULT 'valid' COMMENT '数据状态：valid/invalid/pending',
    ExtractTime DATETIME COMMENT '原始数据抽取时间',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_project (ProjectGUID),
    INDEX idx_cost_element (CostElement),
    INDEX idx_cost_center (CostCenter),
    INDEX idx_fiscal_year (FiscalYear),
    INDEX idx_period (Period),
    INDEX idx_load_time (LoadTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 总账实际明细表';

-- 7. Dwd_gl_budget_detail 总账预算明细表
-- 预算数据清洗结果，支持财务对比分析
DROP TABLE IF EXISTS Dwd_gl_budget_detail;
CREATE TABLE Dwd_gl_budget_detail (
    GlBudgetKey VARCHAR(64) PRIMARY COMMENT '总账预算主键（代理键）',
    GlBudgetGUID VARCHAR(64) NOT NULL COMMENT '总账预算 GUID（业务键）',
    FiscalYear VARCHAR(4) COMMENT '会计年度',
    RecordType VARCHAR(1) COMMENT '记录类型（标准化）',
    Version VARCHAR(2) COMMENT '版本号',
    Ledger VARCHAR(2) COMMENT '分类账',
    Period INT COMMENT '期间',
    CostElement VARCHAR(10) COMMENT '成本要素',
    CostCenter VARCHAR(10) COMMENT '成本中心',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProfitCenter VARCHAR(10) COMMENT '利润中心',
    CurrencyType VARCHAR(1) COMMENT '货币类型',
    BudgetAmountLocal DECIMAL(24,2) COMMENT '预算金额本币（标准化）',
    BudgetAmountTrans DECIMAL(24,2) COMMENT '预算金额交易币（标准化）',
    TransactionCurrency VARCHAR(5) COMMENT '交易货币',
    Quantity DECIMAL(24,3) COMMENT '预算数量',
    Unit VARCHAR(3) COMMENT '数量单位',
    BudgetType VARCHAR(1) COMMENT '预算类型（标准化）',
    BudgetStatus VARCHAR(2) COMMENT '预算状态',
    DataStatus VARCHAR(20) DEFAULT 'valid' COMMENT '数据状态：valid/invalid/pending',
    ExtractTime DATETIME COMMENT '原始数据抽取时间',
    LoadTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加载时间',
    INDEX idx_project (ProjectGUID),
    INDEX idx_cost_element (CostElement),
    INDEX idx_cost_center (CostCenter),
    INDEX idx_fiscal_year (FiscalYear),
    INDEX idx_period (Period),
    INDEX idx_load_time (LoadTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 总账预算明细表';

-- ============================================================
-- 错误数据表（用于归档清洗过程中的异常数据）
-- ============================================================

DROP TABLE IF EXISTS Dwd_error_log;
CREATE TABLE Dwd_error_log (
    ErrorID INT AUTO_INCREMENT PRIMARY KEY COMMENT '错误 ID',
    SourceTable NVARCHAR(100) COMMENT '源表名',
    SourceGUID VARCHAR(64) COMMENT '源数据 GUID',
    ErrorType NVARCHAR(50) COMMENT '错误类型',
    ErrorMsg NVARCHAR(500) COMMENT '错误描述',
    ErrorData TEXT COMMENT '错误数据',
    ErrorTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '错误时间',
    INDEX idx_source (SourceTable, SourceGUID),
    INDEX idx_error_time (ErrorTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 错误数据日志表';
