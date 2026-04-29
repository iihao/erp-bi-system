-- ============================================================
-- ODS 层（操作数据层）数据表设计
-- 依据：论文 4.2.3 节 数据仓库分层表结构设计
-- 说明：ODS 层存放从源系统抽取的原始数据，保持数据的原始形态
--       几乎不做清洗和转换，保证数据的可追溯性
-- ============================================================

-- 创建 ODS 数据库
CREATE DATABASE IF NOT EXISTS erp_ods DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE erp_ods;

-- ============================================================
-- 1. 明源云 ERP 来源表 (6 张)
-- ============================================================

-- 1.1 ODS_room 房间明细表
-- 记录各项目所有房源信息
DROP TABLE IF EXISTS ODS_room;
CREATE TABLE ODS_room (
    RoomGUID VARCHAR(64) PRIMARY KEY COMMENT '房间 GUID',
    RoomNo VARCHAR(50) COMMENT '房间号',
    ProjectGUID VARCHAR(64) COMMENT '项目 GUID',
    ProjectName NVARCHAR(128) COMMENT '项目名称',
    BuildingNo VARCHAR(50) COMMENT '楼栋号',
    BuildingName NVARCHAR(128) COMMENT '楼栋名称',
    UnitNo VARCHAR(50) COMMENT '单元号',
    FloorNo INT COMMENT '楼层号',
    Area DECIMAL(12,2) COMMENT '建筑面积',
    InnerArea DECIMAL(12,2) COMMENT '套内面积',
    PublicArea DECIMAL(12,2) COMMENT '公摊面积',
    RoomType NVARCHAR(50) COMMENT '房型',
    RoomStatus NVARCHAR(50) COMMENT '房间状态',
    Price DECIMAL(14,2) COMMENT '房屋总价',
    UnitPrice DECIMAL(12,2) COMMENT '单价',
    Orientation NVARCHAR(20) COMMENT '朝向',
    Remark NVARCHAR(500) COMMENT '备注',
    CreatedGUID VARCHAR(64) COMMENT '创建人 GUID',
    CreatedName NVARCHAR(50) COMMENT '创建人名称',
    CreatedTime DATETIME COMMENT '创建时间',
    ModifiedGUID VARCHAR(64) COMMENT '修改人 GUID',
    ModifiedName NVARCHAR(50) COMMENT '修改人名称',
    ModifiedTime DATETIME COMMENT '修改时间',
    VersionNumber TIMESTAMP COMMENT '版本号',
    ExtractTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '抽取时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 房间明细表';

-- 1.2 ODS_trade 销售表
-- 记录客户签订售房合同明细信息
DROP TABLE IF EXISTS ODS_trade;
CREATE TABLE ODS_trade (
    TradeGUID VARCHAR(64) PRIMARY KEY COMMENT '交易 GUID',
    BUGUID VARCHAR(64) COMMENT '公司 GUID',
    BuyerAllCardIds NVARCHAR(1024) COMMENT '所有买方证件号码',
    BuyerAllNames NVARCHAR(1024) COMMENT '所有买方姓名',
    CloseReason NVARCHAR(128) COMMENT '关闭原因',
    ContractGUID VARCHAR(64) COMMENT '最后合同 GUID',
    ContractQsDate DATETIME COMMENT '最后合同签署日期',
    ContractYwgsDate DATETIME COMMENT '最后合同业务归属日期',
    IsExistDelayPay INT COMMENT '是否存在延期付款',
    LastGjDate DATETIME COMMENT '最近跟进日期',
    PreTradeGUID VARCHAR(64) COMMENT '前次交易 GUID',
    ProjGUID VARCHAR(64) COMMENT '项目 GUID',
    RGOrderGUID VARCHAR(64) COMMENT '最后认购 GUID',
    RGOrderQsDate DATETIME COMMENT '最后认购日期',
    RGOrderType NVARCHAR(128) COMMENT '最后认购类型',
    RoomGUID VARCHAR(64) COMMENT '房间 GUID',
    RoomStatus NVARCHAR(128) COMMENT '房间状态',
    TradeStatus NVARCHAR(128) COMMENT '交易状态',
    CreatedGUID VARCHAR(64) COMMENT '创建人 GUID',
    CreatedName NVARCHAR(128) COMMENT '创建人名称',
    CreatedTime DATETIME COMMENT '创建时间',
    ModifiedGUID VARCHAR(64) COMMENT '修改人 GUID',
    ModifiedName NVARCHAR(128) COMMENT '修改人名称',
    ModifiedTime DATETIME COMMENT '修改时间',
    VersionNumber TIMESTAMP COMMENT '时间戳',
    ExtractTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '抽取时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 销售表';

-- 1.3 ODS_payment 回款明细表
-- 记录回款明细，包含按揭及公积金款
DROP TABLE IF EXISTS ODS_payment;
CREATE TABLE ODS_payment (
    PayGUID VARCHAR(64) PRIMARY KEY COMMENT '回款 GUID',
    TradeGUID VARCHAR(64) COMMENT '交易 GUID',
    ContractGUID VARCHAR(64) COMMENT '合同 GUID',
    ProjGUID VARCHAR(64) COMMENT '项目 GUID',
    PayAmount DECIMAL(14,2) COMMENT '回款金额',
    PayDate DATETIME COMMENT '回款日期',
    PayType NVARCHAR(50) COMMENT '回款类型',
    PayWay NVARCHAR(50) COMMENT '付款方式',
    BankName NVARCHAR(100) COMMENT '银行名称',
    LoanType NVARCHAR(50) COMMENT '贷款类型',
    PayStatus NVARCHAR(50) COMMENT '回款状态',
    Remark NVARCHAR(500) COMMENT '备注',
    CreatedGUID VARCHAR(64) COMMENT '创建人 GUID',
    CreatedName NVARCHAR(50) COMMENT '创建人名称',
    CreatedTime DATETIME COMMENT '创建时间',
    ModifiedGUID VARCHAR(64) COMMENT '修改人 GUID',
    ModifiedName NVARCHAR(50) COMMENT '修改人名称',
    ModifiedTime DATETIME COMMENT '修改时间',
    VersionNumber TIMESTAMP COMMENT '时间戳',
    ExtractTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '抽取时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 回款明细表';

-- 1.4 ODS_pay 付款登记表
-- 包含合同付款、对公请款、发票报销付款
DROP TABLE IF EXISTS ODS_pay;
CREATE TABLE ODS_pay (
    PayRegGUID VARCHAR(64) PRIMARY KEY COMMENT '付款登记 GUID',
    ProjGUID VARCHAR(64) COMMENT '项目 GUID',
    ContractGUID VARCHAR(64) COMMENT '合同 GUID',
    PayRegAmount DECIMAL(14,2) COMMENT '付款金额',
    PayRegDate DATETIME COMMENT '付款日期',
    PayType NVARCHAR(50) COMMENT '付款类型',
    PayeeName NVARCHAR(100) COMMENT '收款方名称',
    PayeeBank NVARCHAR(100) COMMENT '收款方银行',
    PayeeAccount NVARCHAR(50) COMMENT '收款方账号',
    InvoiceNo NVARCHAR(50) COMMENT '发票号码',
    PayStatus NVARCHAR(50) COMMENT '付款状态',
    Remark NVARCHAR(500) COMMENT '备注',
    CreatedGUID VARCHAR(64) COMMENT '创建人 GUID',
    CreatedName NVARCHAR(50) COMMENT '创建人名称',
    CreatedTime DATETIME COMMENT '创建时间',
    ModifiedGUID VARCHAR(64) COMMENT '修改人 GUID',
    ModifiedName NVARCHAR(50) COMMENT '修改人名称',
    ModifiedTime DATETIME COMMENT '修改时间',
    VersionNumber TIMESTAMP COMMENT '时间戳',
    ExtractTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '抽取时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 付款登记表';

-- 1.5 ODS_account 科目表
-- 记录财务科目，与成本费用科目对应
DROP TABLE IF EXISTS ODS_account;
CREATE TABLE ODS_account (
    AccountGUID VARCHAR(64) PRIMARY KEY COMMENT '科目 GUID',
    AccountCode NVARCHAR(50) COMMENT '科目编码',
    AccountName NVARCHAR(100) COMMENT '科目名称',
    AccountType NVARCHAR(50) COMMENT '科目类型',
    ParentGUID VARCHAR(64) COMMENT '上级科目 GUID',
    Level INT COMMENT '科目级次',
    IsLeaf TINYINT COMMENT '是否末级科目',
    ProjGUID VARCHAR(64) COMMENT '项目 GUID',
    Status NVARCHAR(50) COMMENT '状态',
    Remark NVARCHAR(500) COMMENT '备注',
    CreatedGUID VARCHAR(64) COMMENT '创建人 GUID',
    CreatedName NVARCHAR(50) COMMENT '创建人名称',
    CreatedTime DATETIME COMMENT '创建时间',
    ModifiedGUID VARCHAR(64) COMMENT '修改人 GUID',
    ModifiedName NVARCHAR(50) COMMENT '修改人名称',
    ModifiedTime DATETIME COMMENT '修改时间',
    VersionNumber TIMESTAMP COMMENT '时间戳',
    ExtractTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '抽取时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 科目表';

-- 1.6 ODS_contract 合同表
-- 记录成本及费用产生过程中的合同
DROP TABLE IF EXISTS ODS_contract;
CREATE TABLE ODS_contract (
    ContractGUID VARCHAR(64) PRIMARY KEY COMMENT '合同 GUID',
    ContractCode NVARCHAR(50) COMMENT '合同编码',
    ContractName NVARCHAR(200) COMMENT '合同名称',
    ContractType NVARCHAR(50) COMMENT '合同类型',
    ProjGUID VARCHAR(64) COMMENT '项目 GUID',
    PartyA NVARCHAR(100) COMMENT '甲方',
    PartyB NVARCHAR(100) COMMENT '乙方',
    SignDate DATETIME COMMENT '签订日期',
    StartDate DATETIME COMMENT '开始日期',
    EndDate DATETIME COMMENT '结束日期',
    ContractAmount DECIMAL(14,2) COMMENT '合同金额',
    PaidAmount DECIMAL(14,2) COMMENT '已付金额',
    UnpaidAmount DECIMAL(14,2) COMMENT '未付金额',
    AccountGUID VARCHAR(64) COMMENT '科目 GUID',
    ContractStatus NVARCHAR(50) COMMENT '合同状态',
    Remark NVARCHAR(500) COMMENT '备注',
    CreatedGUID VARCHAR(64) COMMENT '创建人 GUID',
    CreatedName NVARCHAR(50) COMMENT '创建人名称',
    CreatedTime DATETIME COMMENT '创建时间',
    ModifiedGUID VARCHAR(64) COMMENT '修改人 GUID',
    ModifiedName NVARCHAR(50) COMMENT '修改人名称',
    ModifiedTime DATETIME COMMENT '修改时间',
    VersionNumber TIMESTAMP COMMENT '时间戳',
    ExtractTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '抽取时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 合同表';

-- ============================================================
-- 2. SAP 财务软件来源表 (2 张)
-- ============================================================

-- 2.1 ODS_bseg 凭证表
-- 记录财务凭证的详细行项目信息，包括科目、金额、借贷方向等
DROP TABLE IF EXISTS ODS_bseg;
CREATE TABLE ODS_bseg (
    BsegGUID VARCHAR(64) PRIMARY KEY COMMENT '凭证行 GUID',
    Bukrs VARCHAR(4) COMMENT '公司代码',
    Belnr VARCHAR(10) COMMENT '凭证编号',
    Gjahr VARCHAR(4) COMMENT '会计年度',
    Buzei VARCHAR(2) COMMENT '凭证行号',
    HKONT VARCHAR(10) COMMENT '总账科目',
    Sghsl DECIMAL(24,2) COMMENT '成本金额',
    Wrbsl DECIMAL(24,2) COMMENT '成本数量',
    Meins VARCHAR(3) COMMENT '成本单位',
    Kstar VARCHAR(10) COMMENT '成本要素',
    Kostl VARCHAR(10) COMMENT '成本中心',
    ProjGUID VARCHAR(64) COMMENT '项目 GUID',
    Bldat DATETIME COMMENT '凭证过账日期',
    Budat DATETIME COMMENT '记账日期',
    Shkzg VARCHAR(1) COMMENT '借贷标识',
    Bstat VARCHAR(2) COMMENT '凭证状态',
    Xblnr VARCHAR(16) COMMENT '参考凭证编号',
    Sgut1 NVARCHAR(50) COMMENT '分配字段',
    Txt50 NVARCHAR(50) COMMENT '行项目文本',
    ExtractTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '抽取时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 凭证表';

-- 2.2 ODS_GL_Actual 总账实际业务表
-- 整合总账模块的实际业务数据
DROP TABLE IF EXISTS ODS_GL_Actual;
CREATE TABLE ODS_GL_Actual (
    GlActualGUID VARCHAR(64) PRIMARY KEY COMMENT '总账实际业务 GUID',
    RYear VARCHAR(4) COMMENT '会计年度',
    Rcver VARCHAR(3) COMMENT '范围',
    Tvers VARCHAR(2) COMMENT '版本号',
    Lednr VARCHAR(2) COMMENT '分类账',
    Rdart VARCHAR(1) COMMENT '记录类型',
    Sltpo INT COMMENT '期间',
    HkmtArt VARCHAR(1) COMMENT '记账码',
    HkmtNr VARCHAR(4) COMMENT '记账码编号',
    Kstar VARCHAR(10) COMMENT '成本要素',
    Kostl VARCHAR(10) COMMENT '成本中心',
    ProjGUID VARCHAR(64) COMMENT '项目 GUID',
    Prctr VARCHAR(10) COMMENT '利润中心',
    CurrType VARCHAR(1) COMMENT '货币类型',
    Hsl DECIMAL(24,2) COMMENT '实际金额本币',
    Ksl DECIMAL(24,2) COMMENT '实际金额交易币',
    Osl DECIMAL(24,2) COMMENT '实际金额对象币',
    Twaer VARCHAR(5) COMMENT '交易货币',
    Menge DECIMAL(24,3) COMMENT '数量',
    Meins VARCHAR(3) COMMENT '数量单位',
    ExtractTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '抽取时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 总账实际业务表';

-- ============================================================
-- 3. 备用表 (1 张)
-- ============================================================

-- 3.1 ODS_Other 其他数据表
-- 用作手动填报数据
DROP TABLE IF EXISTS ODS_Other;
CREATE TABLE ODS_Other (
    OtherGUID VARCHAR(64) PRIMARY KEY COMMENT '其他数据 GUID',
    DataType NVARCHAR(50) COMMENT '数据类型',
    ProjGUID VARCHAR(64) COMMENT '项目 GUID',
    Field1 NVARCHAR(500) COMMENT '备用字段 1',
    Field2 NVARCHAR(500) COMMENT '备用字段 2',
    Field3 NVARCHAR(500) COMMENT '备用字段 3',
    Field4 DECIMAL(14,2) COMMENT '备用字段 4',
    Field5 DECIMAL(14,2) COMMENT '备用字段 5',
    DateField1 DATETIME COMMENT '备用日期字段 1',
    DateField2 DATETIME COMMENT '备用日期字段 2',
    Remark NVARCHAR(1000) COMMENT '备注',
    CreatedGUID VARCHAR(64) COMMENT '创建人 GUID',
    CreatedName NVARCHAR(50) COMMENT '创建人名称',
    CreatedTime DATETIME COMMENT '创建时间',
    ModifiedGUID VARCHAR(64) COMMENT '修改人 GUID',
    ModifiedName NVARCHAR(50) COMMENT '修改人名称',
    ModifiedTime DATETIME COMMENT '修改时间',
    ExtractTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '抽取时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 其他数据表';
