-- 地产行业商业智能报表系统 - 数据仓库表结构设计 (MySQL 版本)
-- 基于黄强论文《基于 ERP 的地产行业商业智能报表系统的设计与实现》
-- 数据库：MySQL 8.0
-- 创建时间：2026-03-18

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. ODS 层（操作数据层）- 9 张表
-- ============================================

-- 1.1 ODS_room 房间明细表（明源云）
CREATE TABLE IF NOT EXISTS ods_room (
    room_guid VARCHAR(64) PRIMARY KEY COMMENT '房间 GUID',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    building_code VARCHAR(50) COMMENT '楼栋编码',
    room_code VARCHAR(50) COMMENT '房间编码',
    room_name VARCHAR(100) COMMENT '房间名称',
    floor INT COMMENT '楼层',
    unit_number INT COMMENT '房号',
    room_type VARCHAR(50) COMMENT '房间类型',
    building_area DECIMAL(10,2) COMMENT '建筑面积',
    internal_area DECIMAL(10,2) COMMENT '套内面积',
    share_area DECIMAL(10,2) COMMENT '公摊面积',
    orientation VARCHAR(20) COMMENT '朝向',
    total_price DECIMAL(15,2) COMMENT '总价',
    unit_price DECIMAL(12,2) COMMENT '单价',
    room_status VARCHAR(50) COMMENT '房间状态',
    created_time DATETIME COMMENT '创建时间',
    modified_time DATETIME COMMENT '修改时间',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 房间明细表';

CREATE INDEX idx_ods_room_project ON ods_room(project_guid);
CREATE INDEX idx_ods_room_status ON ods_room(room_status);
CREATE INDEX idx_ods_room_dt ON ods_room(dt);

-- 1.2 ODS_trade 销售表（明源云）
CREATE TABLE IF NOT EXISTS ods_trade (
    trade_guid VARCHAR(64) PRIMARY KEY COMMENT '交易 GUID',
    buguid VARCHAR(64) COMMENT '公司 GUID',
    contract_guid VARCHAR(64) COMMENT '合同 GUID',
    room_guid VARCHAR(64) COMMENT '房间 GUID',
    proj_guid VARCHAR(64) COMMENT '项目 GUID',
    buyer_all_names TEXT COMMENT '所有买方姓名',
    buyer_all_card_ids TEXT COMMENT '所有买方证件号码',
    trade_status VARCHAR(50) COMMENT '交易状态',
    close_reason VARCHAR(128) COMMENT '关闭原因',
    contract_qs_date DATETIME COMMENT '合同签署日期',
    contract_ywgs_date DATETIME COMMENT '合同业务归属日期',
    pre_trade_guid VARCHAR(64) COMMENT '前次交易 GUID',
    rgorder_guid VARCHAR(64) COMMENT '认购 GUID',
    rgorder_qs_date DATETIME COMMENT '认购日期',
    rgorder_type VARCHAR(128) COMMENT '认购类型',
    room_status VARCHAR(128) COMMENT '房间状态',
    is_exist_delay_pay INT COMMENT '是否存在延期付款',
    last_gj_date DATETIME COMMENT '最近跟进日期',
    created_guid VARCHAR(64) COMMENT '创建人 GUID',
    created_name VARCHAR(128) COMMENT '创建人名称',
    created_time DATETIME COMMENT '创建时间',
    modified_guid VARCHAR(64) COMMENT '修改人 GUID',
    modified_name VARCHAR(128) COMMENT '修改人名称',
    modified_time DATETIME COMMENT '修改时间',
    version_number BIGINT COMMENT '版本号',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 销售表';

CREATE INDEX idx_ods_trade_contract ON ods_trade(contract_guid);
CREATE INDEX idx_ods_trade_room ON ods_trade(room_guid);
CREATE INDEX idx_ods_trade_project ON ods_trade(proj_guid);
CREATE INDEX idx_ods_trade_status ON ods_trade(trade_status);
CREATE INDEX idx_ods_trade_dt ON ods_trade(dt);

-- 1.3 ODS_payment 回款明细表（明源云）
CREATE TABLE IF NOT EXISTS ods_payment (
    payment_guid VARCHAR(64) PRIMARY KEY COMMENT '收款 GUID',
    contract_guid VARCHAR(64) COMMENT '合同 GUID',
    proj_guid VARCHAR(64) COMMENT '项目 GUID',
    customer_guid VARCHAR(64) COMMENT '客户 GUID',
    payment_amount DECIMAL(15,2) COMMENT '收款金额',
    payment_date DATETIME COMMENT '收款日期',
    payment_type VARCHAR(50) COMMENT '收款类型',
    payment_method VARCHAR(50) COMMENT '收款方式',
    bank_account VARCHAR(100) COMMENT '收款账户',
    invoice_number VARCHAR(100) COMMENT '发票号码',
    invoice_date DATETIME COMMENT '开票日期',
    remarks TEXT COMMENT '备注',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 回款明细表';

CREATE INDEX idx_ods_payment_contract ON ods_payment(contract_guid);
CREATE INDEX idx_ods_payment_project ON ods_payment(proj_guid);
CREATE INDEX idx_ods_payment_date ON ods_payment(payment_date);
CREATE INDEX idx_ods_payment_dt ON ods_payment(dt);

-- 1.4 ODS_pay 付款登记表（明源云）
CREATE TABLE IF NOT EXISTS ods_pay (
    pay_guid VARCHAR(64) PRIMARY KEY COMMENT '付款 GUID',
    contract_guid VARCHAR(64) COMMENT '合同 GUID',
    proj_guid VARCHAR(64) COMMENT '项目 GUID',
    pay_amount DECIMAL(15,2) COMMENT '付款金额',
    pay_date DATETIME COMMENT '付款日期',
    pay_type VARCHAR(50) COMMENT '付款类型',
    payee_name VARCHAR(200) COMMENT '收款方名称',
    payee_account VARCHAR(100) COMMENT '收款方账户',
    invoice_flag INT COMMENT '是否开票',
    invoice_number VARCHAR(100) COMMENT '发票号码',
    remarks TEXT COMMENT '备注',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 付款登记表';

CREATE INDEX idx_ods_pay_contract ON ods_pay(contract_guid);
CREATE INDEX idx_ods_pay_project ON ods_pay(proj_guid);
CREATE INDEX idx_ods_pay_dt ON ods_pay(dt);

-- 1.5 ODS_contract 合同表（明源云）
CREATE TABLE IF NOT EXISTS ods_contract (
    contract_guid VARCHAR(64) PRIMARY KEY COMMENT '合同 GUID',
    proj_guid VARCHAR(64) COMMENT '项目 GUID',
    room_guid VARCHAR(64) COMMENT '房间 GUID',
    customer_guid VARCHAR(64) COMMENT '客户 GUID',
    contract_code VARCHAR(100) COMMENT '合同编号',
    contract_type VARCHAR(50) COMMENT '合同类型',
    contract_amount DECIMAL(15,2) COMMENT '合同金额',
    contract_date DATETIME COMMENT '合同日期',
    contract_status VARCHAR(50) COMMENT '合同状态',
    start_date DATETIME COMMENT '开始日期',
    end_date DATETIME COMMENT '结束日期',
    pay_plan TEXT COMMENT '付款计划',
    remarks TEXT COMMENT '备注',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 合同表';

CREATE INDEX idx_ods_contract_project ON ods_contract(proj_guid);
CREATE INDEX idx_ods_contract_room ON ods_contract(room_guid);
CREATE INDEX idx_ods_contract_status ON ods_contract(contract_status);
CREATE INDEX idx_ods_contract_dt ON ods_contract(dt);

-- 1.6 ODS_account 科目表（明源云）
CREATE TABLE IF NOT EXISTS ods_account (
    account_guid VARCHAR(64) PRIMARY KEY COMMENT '科目 GUID',
    account_code VARCHAR(50) COMMENT '科目编码',
    account_name VARCHAR(200) COMMENT '科目名称',
    account_type VARCHAR(50) COMMENT '科目类型',
    parent_account_guid VARCHAR(64) COMMENT '上级科目 GUID',
    level INT COMMENT '层级',
    balance_direction VARCHAR(20) COMMENT '余额方向',
    is_leaf INT COMMENT '是否叶子节点',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 科目表';

CREATE INDEX idx_ods_account_code ON ods_account(account_code);
CREATE INDEX idx_ods_account_type ON ods_account(account_type);
CREATE INDEX idx_ods_account_dt ON ods_account(dt);

-- 1.7 ODS_bseg 凭证表（SAP）
CREATE TABLE IF NOT EXISTS ods_bseg (
    belnr VARCHAR(20) COMMENT '凭证编号',
    buzei INT COMMENT '行项目号',
    bukrs VARCHAR(10) COMMENT '公司代码',
    gjahr INT COMMENT '会计年度',
    hkont VARCHAR(20) COMMENT '科目号',
    shkzg VARCHAR(1) COMMENT '借贷标识',
    dmbtr DECIMAL(15,2) COMMENT '本位币金额',
    wrbtr DECIMAL(15,2) COMMENT '交易货币金额',
    waers VARCHAR(5) COMMENT '货币',
    kosta VARCHAR(20) COMMENT '成本要素',
    kostl VARCHAR(20) COMMENT '成本中心',
    sgtxt VARCHAR(50) COMMENT '摘要',
    bldat DATETIME COMMENT '凭证日期',
    budat DATETIME COMMENT '过账日期',
    cpudt DATETIME COMMENT '录入时间',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (belnr, buzei, bukrs, gjahr)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - SAP 凭证表';

CREATE INDEX idx_ods_bseg_hkont ON ods_bseg(hkont);
CREATE INDEX idx_ods_bseg_budat ON ods_bseg(budat);
CREATE INDEX idx_ods_bseg_kosta ON ods_bseg(kosta);
CREATE INDEX idx_ods_bseg_dt ON ods_bseg(dt);

-- 1.8 ODS_GL_Actual 总账实际业务表（SAP）
CREATE TABLE IF NOT EXISTS ods_gl_actual (
    gl_guid VARCHAR(64) PRIMARY KEY COMMENT '总账 GUID',
    company_code VARCHAR(10) COMMENT '公司代码',
    fiscal_year INT COMMENT '会计年度',
    document_number VARCHAR(20) COMMENT '凭证号',
    line_item INT COMMENT '行项目',
    account_number VARCHAR(20) COMMENT '科目号',
    account_name VARCHAR(200) COMMENT '科目名称',
    cost_center VARCHAR(20) COMMENT '成本中心',
    profit_center VARCHAR(20) COMMENT '利润中心',
    gl_amount DECIMAL(15,2) COMMENT '原币金额',
    local_amount DECIMAL(15,2) COMMENT '本位币金额',
    currency VARCHAR(5) COMMENT '货币',
    posting_date DATETIME COMMENT '过账日期',
    document_date DATETIME COMMENT '凭证日期',
    text_field TEXT COMMENT '文本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - SAP 总账实际业务表';

CREATE INDEX idx_ods_gl_actual_account ON ods_gl_actual(account_number);
CREATE INDEX idx_ods_gl_actual_cost_center ON ods_gl_actual(cost_center);
CREATE INDEX idx_ods_gl_actual_date ON ods_gl_actual(posting_date);
CREATE INDEX idx_ods_gl_actual_dt ON ods_gl_actual(dt);

-- 1.9 ODS_Other 其他数据表（Excel 填报）
CREATE TABLE IF NOT EXISTS ods_other (
    other_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增 ID',
    data_type VARCHAR(50) COMMENT '数据类型',
    data_content TEXT COMMENT '数据内容',
    fill_user VARCHAR(100) COMMENT '填报人',
    fill_date DATETIME COMMENT '填报日期',
    remarks TEXT COMMENT '备注',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 层 - 其他数据表';

CREATE INDEX idx_ods_other_type ON ods_other(data_type);
CREATE INDEX idx_ods_other_date ON ods_other(fill_date);
CREATE INDEX idx_ods_other_dt ON ods_other(dt);

-- ============================================
-- 2. DWD 层（明细数据层）- 7 张表
-- ============================================

-- 2.1 DWD_room_detail 房源明细表
CREATE TABLE IF NOT EXISTS dwd_room_detail (
    room_key VARCHAR(64) PRIMARY KEY COMMENT '房源主键',
    room_guid VARCHAR(64) COMMENT '房间 GUID',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    building_code VARCHAR(50) COMMENT '楼栋编码',
    room_code VARCHAR(50) COMMENT '房间编码',
    room_name VARCHAR(100) COMMENT '房间名称',
    floor INT COMMENT '楼层',
    unit_number INT COMMENT '房号',
    room_type VARCHAR(50) COMMENT '房间类型',
    building_area DECIMAL(10,2) COMMENT '建筑面积',
    internal_area DECIMAL(10,2) COMMENT '套内面积',
    share_area DECIMAL(10,2) COMMENT '公摊面积',
    orientation VARCHAR(20) COMMENT '朝向',
    total_price DECIMAL(15,2) COMMENT '总价',
    unit_price DECIMAL(12,2) COMMENT '单价',
    room_status VARCHAR(50) COMMENT '房间状态',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project (project_guid),
    INDEX idx_status (room_status),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 房源明细表';

-- 2.2 DWD_trade_detail 销售明细表
CREATE TABLE IF NOT EXISTS dwd_trade_detail (
    trade_key VARCHAR(64) PRIMARY KEY COMMENT '交易主键',
    trade_guid VARCHAR(64) COMMENT '交易 GUID',
    contract_guid VARCHAR(64) COMMENT '合同 GUID',
    room_guid VARCHAR(64) COMMENT '房间 GUID',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    customer_name VARCHAR(200) COMMENT '客户姓名',
    customer_id_type VARCHAR(50) COMMENT '证件类型',
    customer_id_number VARCHAR(100) COMMENT '证件号码',
    trade_status VARCHAR(50) COMMENT '交易状态',
    contract_sign_date DATETIME COMMENT '合同签署日期',
    contract_business_date DATETIME COMMENT '合同业务归属日期',
    subscription_guid VARCHAR(64) COMMENT '认购 GUID',
    subscription_date DATETIME COMMENT '认购日期',
    subscription_type VARCHAR(128) COMMENT '认购类型',
    total_price DECIMAL(15,2) COMMENT '总价',
    area DECIMAL(10,2) COMMENT '面积',
    unit_price DECIMAL(12,2) COMMENT '单价',
    is_delay_pay INT COMMENT '是否延期付款',
    last_follow_date DATETIME COMMENT '最后跟进日期',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project (project_guid),
    INDEX idx_status (trade_status),
    INDEX idx_date (contract_sign_date),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 销售明细表';

-- 2.3 DWD_payment_detail 回款明细表
CREATE TABLE IF NOT EXISTS dwd_payment_detail (
    payment_key VARCHAR(64) PRIMARY KEY COMMENT '收款主键',
    payment_guid VARCHAR(64) COMMENT '收款 GUID',
    contract_guid VARCHAR(64) COMMENT '合同 GUID',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    customer_guid VARCHAR(64) COMMENT '客户 GUID',
    customer_name VARCHAR(200) COMMENT '客户姓名',
    payment_amount DECIMAL(15,2) COMMENT '收款金额',
    payment_date DATETIME COMMENT '收款日期',
    payment_type VARCHAR(50) COMMENT '收款类型',
    payment_method VARCHAR(50) COMMENT '收款方式',
    bank_account VARCHAR(100) COMMENT '收款账户',
    invoice_number VARCHAR(100) COMMENT '发票号码',
    invoice_date DATETIME COMMENT '开票日期',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project (project_guid),
    INDEX idx_date (payment_date),
    INDEX idx_type (payment_type),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 回款明细表';

-- 2.4 DWD_contract_detail 合同明细表
CREATE TABLE IF NOT EXISTS dwd_contract_detail (
    contract_key VARCHAR(64) PRIMARY KEY COMMENT '合同主键',
    contract_guid VARCHAR(64) COMMENT '合同 GUID',
    proj_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    room_guid VARCHAR(64) COMMENT '房间 GUID',
    customer_guid VARCHAR(64) COMMENT '客户 GUID',
    customer_name VARCHAR(200) COMMENT '客户姓名',
    contract_code VARCHAR(100) COMMENT '合同编号',
    contract_type VARCHAR(50) COMMENT '合同类型',
    contract_amount DECIMAL(15,2) COMMENT '合同金额',
    contract_date DATETIME COMMENT '合同日期',
    contract_status VARCHAR(50) COMMENT '合同状态',
    start_date DATETIME COMMENT '开始日期',
    end_date DATETIME COMMENT '结束日期',
    pay_plan TEXT COMMENT '付款计划',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project (proj_guid),
    INDEX idx_status (contract_status),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 合同明细表';

-- 2.5 DWD_pay_detail 付款明细表
CREATE TABLE IF NOT EXISTS dwd_pay_detail (
    pay_key VARCHAR(64) PRIMARY KEY COMMENT '付款主键',
    pay_guid VARCHAR(64) COMMENT '付款 GUID',
    contract_guid VARCHAR(64) COMMENT '合同 GUID',
    proj_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    pay_amount DECIMAL(15,2) COMMENT '付款金额',
    pay_date DATETIME COMMENT '付款日期',
    pay_type VARCHAR(50) COMMENT '付款类型',
    payee_name VARCHAR(200) COMMENT '收款方名称',
    payee_account VARCHAR(100) COMMENT '收款方账户',
    invoice_flag INT COMMENT '是否开票',
    invoice_number VARCHAR(100) COMMENT '发票号码',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project (proj_guid),
    INDEX idx_date (pay_date),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 付款明细表';

-- 2.6 DWD_gl_actual_detail 总账实际明细表
CREATE TABLE IF NOT EXISTS dwd_gl_actual_detail (
    gl_key VARCHAR(64) PRIMARY KEY COMMENT '总账主键',
    gl_guid VARCHAR(64) COMMENT '总账 GUID',
    company_code VARCHAR(10) COMMENT '公司代码',
    fiscal_year INT COMMENT '会计年度',
    document_number VARCHAR(20) COMMENT '凭证号',
    line_item INT COMMENT '行项目',
    account_number VARCHAR(20) COMMENT '科目号',
    account_name VARCHAR(200) COMMENT '科目名称',
    cost_center VARCHAR(20) COMMENT '成本中心',
    cost_center_name VARCHAR(200) COMMENT '成本中心名称',
    profit_center VARCHAR(20) COMMENT '利润中心',
    gl_amount DECIMAL(15,2) COMMENT '原币金额',
    local_amount DECIMAL(15,2) COMMENT '本位币金额',
    currency VARCHAR(5) COMMENT '货币',
    posting_date DATETIME COMMENT '过账日期',
    document_date DATETIME COMMENT '凭证日期',
    text_field TEXT COMMENT '文本',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_account (account_number),
    INDEX idx_cost_center (cost_center),
    INDEX idx_date (posting_date),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 总账实际明细表';

-- 2.7 DWD_gl_budget_detail 总账预算明细表
CREATE TABLE IF NOT EXISTS dwd_gl_budget_detail (
    budget_key VARCHAR(64) PRIMARY KEY COMMENT '预算主键',
    budget_guid VARCHAR(64) COMMENT '预算 GUID',
    company_code VARCHAR(10) COMMENT '公司代码',
    fiscal_year INT COMMENT '会计年度',
    account_number VARCHAR(20) COMMENT '科目号',
    account_name VARCHAR(200) COMMENT '科目名称',
    cost_center VARCHAR(20) COMMENT '成本中心',
    budget_amount DECIMAL(15,2) COMMENT '预算金额',
    budget_version VARCHAR(50) COMMENT '预算版本',
    budget_type VARCHAR(50) COMMENT '预算类型',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_account (account_number),
    INDEX idx_year (fiscal_year),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 层 - 总账预算明细表';

-- ============================================
-- 3. DWS 层（服务数据层）- 5 张表
-- ============================================

-- 3.1 DWS_sales_payment_fact 销售 - 回款事实表
CREATE TABLE IF NOT EXISTS dws_sales_payment_fact (
    fact_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '事实 ID',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    contract_guid VARCHAR(64) COMMENT '合同 GUID',
    customer_guid VARCHAR(64) COMMENT '客户 GUID',
    date_key DATE COMMENT '日期键',
    year INT COMMENT '年',
    month INT COMMENT '月',
    day INT COMMENT '日',
    contract_amount DECIMAL(15,2) COMMENT '合同金额',
    payment_amount DECIMAL(15,2) COMMENT '回款金额',
    payment_rate DECIMAL(5,2) COMMENT '回款率',
    contract_count INT COMMENT '合同数量',
    payment_count INT COMMENT '回款数量',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project (project_guid),
    INDEX idx_date (date_key),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 层 - 销售回款事实表';

-- 3.2 DWS_sales_cost_fact 成本 - 费用事实表
CREATE TABLE IF NOT EXISTS dws_sales_cost_fact (
    fact_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '事实 ID',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    contract_guid VARCHAR(64) COMMENT '合同 GUID',
    account_number VARCHAR(20) COMMENT '科目号',
    account_name VARCHAR(200) COMMENT '科目名称',
    cost_center VARCHAR(20) COMMENT '成本中心',
    date_key DATE COMMENT '日期键',
    year INT COMMENT '年',
    month INT COMMENT '月',
    day INT COMMENT '日',
    contract_amount DECIMAL(15,2) COMMENT '合同金额',
    cost_amount DECIMAL(15,2) COMMENT '成本金额',
    fee_amount DECIMAL(15,2) COMMENT '费用金额',
    budget_amount DECIMAL(15,2) COMMENT '预算金额',
    budget_variance DECIMAL(15,2) COMMENT '预算差异',
    variance_rate DECIMAL(5,2) COMMENT '差异率',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project (project_guid),
    INDEX idx_account (account_number),
    INDEX idx_date (date_key),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 层 - 成本费用事实表';

-- 3.3 Dim_project 项目维度表
CREATE TABLE IF NOT EXISTS dim_project (
    project_guid VARCHAR(64) PRIMARY KEY COMMENT '项目 GUID',
    project_code VARCHAR(50) COMMENT '项目编码',
    project_name VARCHAR(200) COMMENT '项目名称',
    city VARCHAR(100) COMMENT '城市',
    district VARCHAR(100) COMMENT '区域',
    product_type VARCHAR(50) COMMENT '产品业态',
    building_type VARCHAR(50) COMMENT '楼栋类型',
    total_area DECIMAL(15,2) COMMENT '总建筑面积',
    total_units INT COMMENT '总户数',
    developer VARCHAR(200) COMMENT '开发商',
    property_management VARCHAR(200) COMMENT '物业公司',
    start_date DATE COMMENT '开工日期',
    expected_completion DATE COMMENT '预计竣工日期',
    actual_completion DATE COMMENT '实际竣工日期',
    project_status VARCHAR(50) COMMENT '项目状态',
    is_active INT DEFAULT 1 COMMENT '是否有效',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_city (city),
    INDEX idx_status (project_status),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='维度表 - 项目维度';

-- 3.4 Dim_date 时间维度表
CREATE TABLE IF NOT EXISTS dim_date (
    date_key DATE PRIMARY KEY COMMENT '日期键',
    year INT COMMENT '年',
    quarter INT COMMENT '季度',
    month INT COMMENT '月',
    day INT COMMENT '日',
    week_of_year INT COMMENT '一年中的第几周',
    day_of_week INT COMMENT '一周中的第几天',
    day_name VARCHAR(20) COMMENT '星期名称',
    month_name VARCHAR(20) COMMENT '月份名称',
    is_weekend INT COMMENT '是否周末',
    is_holiday INT COMMENT '是否节假日',
    holiday_name VARCHAR(100) COMMENT '节假日名称',
    fiscal_year INT COMMENT '财务年度',
    fiscal_quarter INT COMMENT '财务季度',
    fiscal_month INT COMMENT '财务月份',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_year (year),
    INDEX idx_month (month),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='维度表 - 时间维度';

-- 3.5 Dim_account 科目维度表
CREATE TABLE IF NOT EXISTS dim_account (
    account_guid VARCHAR(64) PRIMARY KEY COMMENT '科目 GUID',
    account_code VARCHAR(50) COMMENT '科目编码',
    account_name VARCHAR(200) COMMENT '科目名称',
    account_type VARCHAR(50) COMMENT '科目类型',
    parent_account_guid VARCHAR(64) COMMENT '上级科目 GUID',
    parent_account_code VARCHAR(50) COMMENT '上级科目编码',
    parent_account_name VARCHAR(200) COMMENT '上级科目名称',
    level INT COMMENT '层级',
    balance_direction VARCHAR(20) COMMENT '余额方向',
    is_leaf INT DEFAULT 1 COMMENT '是否叶子节点',
    full_path TEXT COMMENT '完整路径',
    is_active INT DEFAULT 1 COMMENT '是否有效',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_code (account_code),
    INDEX idx_type (account_type),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='维度表 - 科目维度';

-- ============================================
-- 4. ADS 层（应用数据层）- 7 张表
-- ============================================

-- 4.1 Ads_group_sales_report 集团销售目标达成表
CREATE TABLE IF NOT EXISTS ads_group_sales_report (
    report_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '报表 ID',
    report_date DATE COMMENT '报表日期',
    year INT COMMENT '年',
    month INT COMMENT '月',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    city VARCHAR(100) COMMENT '城市',
    target_amount DECIMAL(15,2) COMMENT '目标金额',
    actual_amount DECIMAL(15,2) COMMENT '实际金额',
    achievement_rate DECIMAL(5,2) COMMENT '达成率',
    contract_count INT COMMENT '合同数量',
    area DECIMAL(10,2) COMMENT '面积',
    unit_price DECIMAL(12,2) COMMENT '单价',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (report_date),
    INDEX idx_project (project_guid),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 集团销售目标达成表';

-- 4.2 Ads_group_salesdate_report 集团签约回款周月年报
CREATE TABLE IF NOT EXISTS ads_group_salesdate_report (
    report_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '报表 ID',
    report_type VARCHAR(20) COMMENT '报表类型：daily/weekly/monthly/yearly',
    report_year INT COMMENT '报表年份',
    report_week INT COMMENT '报表周',
    report_month INT COMMENT '报表月份',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    contract_amount DECIMAL(15,2) COMMENT '合同金额',
    payment_amount DECIMAL(15,2) COMMENT '回款金额',
    payment_rate DECIMAL(5,2) COMMENT '回款率',
    contract_count INT COMMENT '合同数量',
    payment_count INT COMMENT '回款数量',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (report_type),
    INDEX idx_project (project_guid),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 集团签约回款周月年报';

-- 4.3 Ads_group_pay_report 集团费用支出汇总表
CREATE TABLE IF NOT EXISTS ads_group_pay_report (
    report_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '报表 ID',
    report_date DATE COMMENT '报表日期',
    year INT COMMENT '年',
    month INT COMMENT '月',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    contract_pay_amount DECIMAL(15,2) COMMENT '合同付款金额',
    fee_amount DECIMAL(15,2) COMMENT '费用金额',
    total_amount DECIMAL(15,2) COMMENT '总金额',
    budget_amount DECIMAL(15,2) COMMENT '预算金额',
    variance_amount DECIMAL(15,2) COMMENT '差异金额',
    variance_rate DECIMAL(5,2) COMMENT '差异率',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (report_date),
    INDEX idx_project (project_guid),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 集团费用支出汇总表';

-- 4.4 Ads_project_cost_report 项目成本费用报表
CREATE TABLE IF NOT EXISTS ads_project_cost_report (
    report_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '报表 ID',
    report_date DATE COMMENT '报表日期',
    year INT COMMENT '年',
    month INT COMMENT '月',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    account_number VARCHAR(20) COMMENT '科目号',
    account_name VARCHAR(200) COMMENT '科目名称',
    cost_type VARCHAR(50) COMMENT '成本类型',
    budget_amount DECIMAL(15,2) COMMENT '预算金额',
    actual_amount DECIMAL(15,2) COMMENT '实际金额',
    variance_amount DECIMAL(15,2) COMMENT '差异金额',
    variance_rate DECIMAL(5,2) COMMENT '差异率',
    completion_rate DECIMAL(5,2) COMMENT '完成率',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (report_date),
    INDEX idx_project (project_guid),
    INDEX idx_account (account_number),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 项目成本费用报表';

-- 4.5 Ads_sales_dashboard 营销驾驶舱大屏
CREATE TABLE IF NOT EXISTS ads_sales_dashboard (
    dashboard_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '驾驶舱 ID',
    dashboard_date DATE COMMENT '驾驶舱日期',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    total_units INT COMMENT '总房源数',
    sold_units INT COMMENT '已售房源数',
    available_units INT COMMENT '可售房源数',
    sell_through_rate DECIMAL(5,2) COMMENT '去化率',
    total_sales DECIMAL(15,2) COMMENT '总销售额',
    total_payment DECIMAL(15,2) COMMENT '总回款',
    payment_rate DECIMAL(5,2) COMMENT '回款率',
    avg_unit_price DECIMAL(12,2) COMMENT '平均单价',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (dashboard_date),
    INDEX idx_project (project_guid),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 营销驾驶舱大屏';

-- 4.6 Ads_finance_dashboard 财务驾驶舱大屏
CREATE TABLE IF NOT EXISTS ads_finance_dashboard (
    dashboard_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '驾驶舱 ID',
    dashboard_date DATE COMMENT '驾驶舱日期',
    company_code VARCHAR(10) COMMENT '公司代码',
    total_revenue DECIMAL(15,2) COMMENT '总收入',
    total_cost DECIMAL(15,2) COMMENT '总成本',
    total_profit DECIMAL(15,2) COMMENT '总利润',
    profit_margin DECIMAL(5,2) COMMENT '利润率',
    total_assets DECIMAL(15,2) COMMENT '总资产',
    total_liabilities DECIMAL(15,2) COMMENT '总负债',
    cash_flow DECIMAL(15,2) COMMENT '现金流',
    budget_execution_rate DECIMAL(5,2) COMMENT '预算执行率',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (dashboard_date),
    INDEX idx_company (company_code),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 财务驾驶舱大屏';

-- 4.7 Ads_szl_dashboard 收支利大屏
CREATE TABLE IF NOT EXISTS ads_szl_dashboard (
    dashboard_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '驾驶舱 ID',
    dashboard_date DATE COMMENT '驾驶舱日期',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    project_name VARCHAR(200) COMMENT '项目名称',
    sales_revenue DECIMAL(15,2) COMMENT '销售收入',
    total_cost DECIMAL(15,2) COMMENT '总成本',
    total_expense DECIMAL(15,2) COMMENT '总费用',
    operating_profit DECIMAL(15,2) COMMENT '营业利润',
    net_profit DECIMAL(15,2) COMMENT '净利润',
    profit_margin DECIMAL(5,2) COMMENT '利润率',
    roi DECIMAL(5,2) COMMENT '投资回报率',
    data_version DATE COMMENT '数据版本',
    dt DATE COMMENT '数据分区日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (dashboard_date),
    INDEX idx_project (project_guid),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS 层 - 收支利大屏';

-- ============================================
-- 5. 辅助表（权限控制 + 指标口径库）
-- ============================================

-- 权限控制表（论文 5.2 节）
CREATE TABLE IF NOT EXISTS dim_permission (
    permission_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '权限 ID',
    user_id VARCHAR(64) COMMENT '用户 ID',
    role_id VARCHAR(64) COMMENT '角色 ID',
    department_id VARCHAR(64) COMMENT '部门 ID',
    project_guid VARCHAR(64) COMMENT '项目 GUID',
    permission_key VARCHAR(100) COMMENT '权限关键字',
    data_scope TEXT COMMENT '数据范围',
    is_active INT DEFAULT 1 COMMENT '是否有效',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    dt DATE COMMENT '数据分区日期',
    INDEX idx_user (user_id),
    INDEX idx_project (project_guid),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='维度表 - 权限控制';

-- 指标口径库（论文 3.2 节）
CREATE TABLE IF NOT EXISTS dim_indicator (
    indicator_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '指标 ID',
    indicator_code VARCHAR(50) UNIQUE COMMENT '指标编码',
    indicator_name VARCHAR(200) COMMENT '指标名称',
    calculation_rule TEXT COMMENT '计算规则',
    formula VARCHAR(500) COMMENT '计算公式',
    unit VARCHAR(20) COMMENT '单位',
    version VARCHAR(50) COMMENT '版本',
    description TEXT COMMENT '说明',
    is_active INT DEFAULT 1 COMMENT '是否有效',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    dt DATE COMMENT '数据分区日期',
    INDEX idx_code (indicator_code),
    INDEX idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='维度表 - 指标口径库';

-- 插入核心指标定义
INSERT INTO dim_indicator (indicator_code, indicator_name, calculation_rule, formula, unit, version, description) VALUES
('IND001', '销售去化率', '已售房源数/总房源数*100%', 'sold_units/total_units*100', '%', 'v1.0', '反映项目销售进度'),
('IND002', '项目回款率', '已回款金额/应收回款金额*100%', 'payment_amount/receivable_amount*100', '%', 'v1.0', '反映项目回款情况'),
('IND003', '合同执行率', '已执行合同金额/合同总金额*100%', 'executed_amount/contract_amount*100', '%', 'v1.0', '反映合同执行情况'),
('IND004', '预算执行率', '实际支出/预算金额*100%', 'actual_amount/budget_amount*100', '%', 'v1.0', '反映预算执行情况'),
('IND005', '销售目标达成率', '实际销售额/目标销售额*100%', 'actual_sales/target_sales*100', '%', 'v1.0', '反映销售目标完成情况'),
('IND006', '毛利率', '(销售收入 - 销售成本)/销售收入*100%', '(revenue-cost)/revenue*100', '%', 'v1.0', '反映项目盈利能力');

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 验证表创建
-- ============================================

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
