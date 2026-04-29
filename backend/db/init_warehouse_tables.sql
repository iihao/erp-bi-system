-- 地产行业商业智能报表系统 - 数据仓库表结构设计
-- 基于黄强论文《基于 ERP 的地产行业商业智能报表系统的设计与实现》
-- 创建时间：2026-03-18

-- ============================================
-- 1. ODS 层（操作数据层）- 9 张表
-- ============================================

-- 1.1 ODS_room 房间明细表（明源云）
CREATE TABLE IF NOT EXISTS ods_room (
    room_guid TEXT PRIMARY KEY,
    project_guid TEXT,
    building_code TEXT,
    room_code TEXT,
    room_name TEXT,
    floor INTEGER,
    unit_number INTEGER,
    room_type TEXT,
    building_area DECIMAL(10,2),
    internal_area DECIMAL(10,2),
    share_area DECIMAL(10,2),
    orientation TEXT,
    total_price DECIMAL(15,2),
    unit_price DECIMAL(12,2),
    room_status TEXT,
    created_time DATETIME,
    modified_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ods_room_project ON ods_room(project_guid);
CREATE INDEX IF NOT EXISTS idx_ods_room_status ON ods_room(room_status);

-- 1.2 ODS_trade 销售表（明源云）
CREATE TABLE IF NOT EXISTS ods_trade (
    trade_guid TEXT PRIMARY KEY,
    buguid TEXT,
    contract_guid TEXT,
    room_guid TEXT,
    proj_guid TEXT,
    buyer_all_names TEXT,
    buyer_all_card_ids TEXT,
    trade_status TEXT,
    close_reason TEXT,
    contract_qs_date DATETIME,
    contract_ywgs_date DATETIME,
    pre_trade_guid TEXT,
    rgorder_guid TEXT,
    rgorder_qs_date DATETIME,
    rgorder_type TEXT,
    room_status TEXT,
    is_exist_delay_pay INTEGER,
    last_gj_date DATETIME,
    created_guid TEXT,
    created_name TEXT,
    created_time DATETIME,
    modified_guid TEXT,
    modified_name TEXT,
    modified_time DATETIME,
    version_number TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ods_trade_contract ON ods_trade(contract_guid);
CREATE INDEX IF NOT EXISTS idx_ods_trade_room ON ods_trade(room_guid);
CREATE INDEX IF NOT EXISTS idx_ods_trade_project ON ods_trade(proj_guid);
CREATE INDEX IF NOT EXISTS idx_ods_trade_status ON ods_trade(trade_status);

-- 1.3 ODS_payment 回款明细表（明源云）
CREATE TABLE IF NOT EXISTS ods_payment (
    payment_guid TEXT PRIMARY KEY,
    contract_guid TEXT,
    proj_guid TEXT,
    customer_guid TEXT,
    payment_amount DECIMAL(15,2),
    payment_date DATETIME,
    payment_type TEXT,
    payment_method TEXT,
    bank_account TEXT,
    invoice_number TEXT,
    invoice_date DATETIME,
    remarks TEXT,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ods_payment_contract ON ods_payment(contract_guid);
CREATE INDEX IF NOT EXISTS idx_ods_payment_project ON ods_payment(proj_guid);
CREATE INDEX IF NOT EXISTS idx_ods_payment_date ON ods_payment(payment_date);

-- 1.4 ODS_pay 付款登记表（明源云）
CREATE TABLE IF NOT EXISTS ods_pay (
    pay_guid TEXT PRIMARY KEY,
    contract_guid TEXT,
    proj_guid TEXT,
    pay_amount DECIMAL(15,2),
    pay_date DATETIME,
    pay_type TEXT,
    payee_name TEXT,
    payee_account TEXT,
    invoice_flag INTEGER,
    invoice_number TEXT,
    remarks TEXT,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ods_pay_contract ON ods_pay(contract_guid);
CREATE INDEX IF NOT EXISTS idx_ods_pay_project ON ods_pay(proj_guid);

-- 1.5 ODS_contract 合同表（明源云）
CREATE TABLE IF NOT EXISTS ods_contract (
    contract_guid TEXT PRIMARY KEY,
    proj_guid TEXT,
    room_guid TEXT,
    customer_guid TEXT,
    contract_code TEXT,
    contract_type TEXT,
    contract_amount DECIMAL(15,2),
    contract_date DATETIME,
    contract_status TEXT,
    start_date DATETIME,
    end_date DATETIME,
    pay_plan TEXT,
    remarks TEXT,
    created_time DATETIME,
    modified_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ods_contract_project ON ods_contract(proj_guid);
CREATE INDEX IF NOT EXISTS idx_ods_contract_room ON ods_contract(room_guid);
CREATE INDEX IF NOT EXISTS idx_ods_contract_status ON ods_contract(contract_status);

-- 1.6 ODS_account 科目表（明源云）
CREATE TABLE IF NOT EXISTS ods_account (
    account_guid TEXT PRIMARY KEY,
    account_code TEXT,
    account_name TEXT,
    account_type TEXT,
    parent_account_guid TEXT,
    level INTEGER,
    balance_direction TEXT,
    is_leaf INTEGER,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ods_account_code ON ods_account(account_code);
CREATE INDEX IF NOT EXISTS idx_ods_account_type ON ods_account(account_type);

-- 1.7 ODS_bseg 凭证表（SAP）
CREATE TABLE IF NOT EXISTS ods_bseg (
    belnr TEXT,
    buzei INTEGER,
    bukrs TEXT,
    gjahr INTEGER,
    hkont TEXT,
    shkzg TEXT,
    dmbtr DECIMAL(15,2),
    wrbtr DECIMAL(15,2),
    waers TEXT,
    kosta TEXT,
    kostl TEXT,
    sgtxt TEXT,
    bldat DATETIME,
    budat DATETIME,
    cpudt DATETIME,
    PRIMARY KEY (belnr, buzei, bukrs, gjahr)
);

CREATE INDEX IF NOT EXISTS idx_ods_bseg_hkont ON ods_bseg(hkont);
CREATE INDEX IF NOT EXISTS idx_ods_bseg_budat ON ods_bseg(budat);
CREATE INDEX IF NOT EXISTS idx_ods_bseg_kosta ON ods_bseg(kosta);

-- 1.8 ODS_GL_Actual 总账实际业务表（SAP）
CREATE TABLE IF NOT EXISTS ods_gl_actual (
    gl_guid TEXT PRIMARY KEY,
    company_code TEXT,
    fiscal_year INTEGER,
    document_number TEXT,
    line_item INTEGER,
    account_number TEXT,
    account_name TEXT,
    cost_center TEXT,
    profit_center TEXT,
    gl_amount DECIMAL(15,2),
    local_amount DECIMAL(15,2),
    currency TEXT,
    posting_date DATETIME,
    document_date DATETIME,
    text_field TEXT,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ods_gl_actual_account ON ods_gl_actual(account_number);
CREATE INDEX IF NOT EXISTS idx_ods_gl_actual_cost_center ON ods_gl_actual(cost_center);
CREATE INDEX IF NOT EXISTS idx_ods_gl_actual_date ON ods_gl_actual(posting_date);

-- 1.9 ODS_Other 其他数据表（Excel 填报）
CREATE TABLE IF NOT EXISTS ods_other (
    other_id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_type TEXT,
    data_content TEXT,
    fill_user TEXT,
    fill_date DATETIME,
    remarks TEXT,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ods_other_type ON ods_other(data_type);
CREATE INDEX IF NOT EXISTS idx_ods_other_date ON ods_other(fill_date);

-- ============================================
-- 2. DWD 层（明细数据层）- 7 张表
-- ============================================

-- 2.1 DWD_room_detail 房源明细表
CREATE TABLE IF NOT EXISTS dwd_room_detail (
    room_key TEXT PRIMARY KEY,
    room_guid TEXT,
    project_guid TEXT,
    project_name TEXT,
    building_code TEXT,
    room_code TEXT,
    room_name TEXT,
    floor INTEGER,
    unit_number INTEGER,
    room_type TEXT,
    building_area DECIMAL(10,2),
    internal_area DECIMAL(10,2),
    share_area DECIMAL(10,2),
    orientation TEXT,
    total_price DECIMAL(15,2),
    unit_price DECIMAL(12,2),
    room_status TEXT,
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_dwd_room_project ON dwd_room_detail(project_guid);
CREATE INDEX IF NOT EXISTS idx_dwd_room_status ON dwd_room_detail(room_status);

-- 2.2 DWD_trade_detail 销售明细表
CREATE TABLE IF NOT EXISTS dwd_trade_detail (
    trade_key TEXT PRIMARY KEY,
    trade_guid TEXT,
    contract_guid TEXT,
    room_guid TEXT,
    project_guid TEXT,
    project_name TEXT,
    customer_name TEXT,
    customer_id_type TEXT,
    customer_id_number TEXT,
    trade_status TEXT,
    contract_sign_date DATETIME,
    contract_business_date DATETIME,
    subscription_guid TEXT,
    subscription_date DATETIME,
    subscription_type TEXT,
    total_price DECIMAL(15,2),
    area DECIMAL(10,2),
    unit_price DECIMAL(12,2),
    is_delay_pay INTEGER,
    last_follow_date DATETIME,
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_dwd_trade_project ON dwd_trade_detail(project_guid);
CREATE INDEX IF NOT EXISTS idx_dwd_trade_status ON dwd_trade_detail(trade_status);
CREATE INDEX IF NOT EXISTS idx_dwd_trade_date ON dwd_trade_detail(contract_sign_date);

-- 2.3 DWD_payment_detail 回款明细表
CREATE TABLE IF NOT EXISTS dwd_payment_detail (
    payment_key TEXT PRIMARY KEY,
    payment_guid TEXT,
    contract_guid TEXT,
    project_guid TEXT,
    project_name TEXT,
    customer_guid TEXT,
    customer_name TEXT,
    payment_amount DECIMAL(15,2),
    payment_date DATETIME,
    payment_type TEXT,
    payment_method TEXT,
    bank_account TEXT,
    invoice_number TEXT,
    invoice_date DATETIME,
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_dwd_payment_project ON dwd_payment_detail(project_guid);
CREATE INDEX IF NOT EXISTS idx_dwd_payment_date ON dwd_payment_detail(payment_date);
CREATE INDEX IF NOT EXISTS idx_dwd_payment_type ON dwd_payment_detail(payment_type);

-- 2.4 DWD_contract_detail 合同明细表
CREATE TABLE IF NOT EXISTS dwd_contract_detail (
    contract_key TEXT PRIMARY KEY,
    contract_guid TEXT,
    proj_guid TEXT,
    project_name TEXT,
    room_guid TEXT,
    customer_guid TEXT,
    customer_name TEXT,
    contract_code TEXT,
    contract_type TEXT,
    contract_amount DECIMAL(15,2),
    contract_date DATETIME,
    contract_status TEXT,
    start_date DATETIME,
    end_date DATETIME,
    pay_plan TEXT,
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_dwd_contract_project ON dwd_contract_detail(proj_guid);
CREATE INDEX IF NOT EXISTS idx_dwd_contract_status ON dwd_contract_detail(contract_status);

-- 2.5 DWD_pay_detail 付款明细表
CREATE TABLE IF NOT EXISTS dwd_pay_detail (
    pay_key TEXT PRIMARY KEY,
    pay_guid TEXT,
    contract_guid TEXT,
    proj_guid TEXT,
    project_name TEXT,
    pay_amount DECIMAL(15,2),
    pay_date DATETIME,
    pay_type TEXT,
    payee_name TEXT,
    payee_account TEXT,
    invoice_flag INTEGER,
    invoice_number TEXT,
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_dwd_pay_project ON dwd_pay_detail(proj_guid);
CREATE INDEX IF NOT EXISTS idx_dwd_pay_date ON dwd_pay_detail(pay_date);

-- 2.6 DWD_gl_actual_detail 总账实际明细表
CREATE TABLE IF NOT EXISTS dwd_gl_actual_detail (
    gl_key TEXT PRIMARY KEY,
    gl_guid TEXT,
    company_code TEXT,
    fiscal_year INTEGER,
    document_number TEXT,
    line_item INTEGER,
    account_number TEXT,
    account_name TEXT,
    cost_center TEXT,
    cost_center_name TEXT,
    profit_center TEXT,
    gl_amount DECIMAL(15,2),
    local_amount DECIMAL(15,2),
    currency TEXT,
    posting_date DATETIME,
    document_date DATETIME,
    text_field TEXT,
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_dwd_gl_account ON dwd_gl_actual_detail(account_number);
CREATE INDEX IF NOT EXISTS idx_dwd_gl_cost_center ON dwd_gl_actual_detail(cost_center);
CREATE INDEX IF NOT EXISTS idx_dwd_gl_date ON dwd_gl_actual_detail(posting_date);

-- 2.7 DWD_gl_budget_detail 总账预算明细表
CREATE TABLE IF NOT EXISTS dwd_gl_budget_detail (
    budget_key TEXT PRIMARY KEY,
    budget_guid TEXT,
    company_code TEXT,
    fiscal_year INTEGER,
    account_number TEXT,
    account_name TEXT,
    cost_center TEXT,
    budget_amount DECIMAL(15,2),
    budget_version TEXT,
    budget_type TEXT,
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_dwd_budget_account ON dwd_gl_budget_detail(account_number);
CREATE INDEX IF NOT EXISTS idx_dwd_budget_year ON dwd_gl_budget_detail(fiscal_year);

-- ============================================
-- 3. DWS 层（服务数据层）- 5 张表
-- ============================================

-- 3.1 DWS_sales_payment_fact 销售 - 回款事实表
CREATE TABLE IF NOT EXISTS dws_sales_payment_fact (
    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_guid TEXT,
    project_name TEXT,
    contract_guid TEXT,
    customer_guid TEXT,
    date_key DATE,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    contract_amount DECIMAL(15,2),
    payment_amount DECIMAL(15,2),
    payment_rate DECIMAL(5,2),
    contract_count INTEGER,
    payment_count INTEGER,
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_dws_sales_project ON dws_sales_payment_fact(project_guid);
CREATE INDEX IF NOT EXISTS idx_dws_sales_date ON dws_sales_payment_fact(date_key);

-- 3.2 DWS_sales_cost_fact 成本 - 费用事实表
CREATE TABLE IF NOT EXISTS dws_sales_cost_fact (
    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_guid TEXT,
    project_name TEXT,
    contract_guid TEXT,
    account_number TEXT,
    account_name TEXT,
    cost_center TEXT,
    date_key DATE,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    contract_amount DECIMAL(15,2),
    cost_amount DECIMAL(15,2),
    fee_amount DECIMAL(15,2),
    budget_amount DECIMAL(15,2),
    budget_variance DECIMAL(15,2),
    variance_rate DECIMAL(5,2),
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_dws_cost_project ON dws_sales_cost_fact(project_guid);
CREATE INDEX IF NOT EXISTS idx_dws_cost_account ON dws_sales_cost_fact(account_number);
CREATE INDEX IF NOT EXISTS idx_dws_cost_date ON dws_sales_cost_fact(date_key);

-- 3.3 Dim_project 项目维度表
CREATE TABLE IF NOT EXISTS dim_project (
    project_guid TEXT PRIMARY KEY,
    project_code TEXT,
    project_name TEXT,
    city TEXT,
    district TEXT,
    product_type TEXT,
    building_type TEXT,
    total_area DECIMAL(15,2),
    total_units INTEGER,
    developer TEXT,
    property_management TEXT,
    start_date DATE,
    expected_completion DATE,
    actual_completion DATE,
    project_status TEXT,
    is_active INTEGER,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_dim_project_city ON dim_project(city);
CREATE INDEX IF NOT EXISTS idx_dim_project_status ON dim_project(project_status);

-- 3.4 Dim_date 时间维度表
CREATE TABLE IF NOT EXISTS dim_date (
    date_key DATE PRIMARY KEY,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    day INTEGER,
    week_of_year INTEGER,
    day_of_week INTEGER,
    day_name TEXT,
    month_name TEXT,
    is_weekend INTEGER,
    is_holiday INTEGER,
    holiday_name TEXT,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    fiscal_month INTEGER
);

-- 3.5 Dim_account 科目维度表
CREATE TABLE IF NOT EXISTS dim_account (
    account_guid TEXT PRIMARY KEY,
    account_code TEXT,
    account_name TEXT,
    account_type TEXT,
    parent_account_guid TEXT,
    parent_account_code TEXT,
    parent_account_name TEXT,
    level INTEGER,
    balance_direction TEXT,
    is_leaf INTEGER,
    full_path TEXT,
    is_active INTEGER,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_dim_account_code ON dim_account(account_code);
CREATE INDEX IF NOT EXISTS idx_dim_account_type ON dim_account(account_type);

-- ============================================
-- 4. ADS 层（应用数据层）- 7 张表
-- ============================================

-- 4.1 Ads_group_sales_report 集团销售目标达成表
CREATE TABLE IF NOT EXISTS ads_group_sales_report (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE,
    year INTEGER,
    month INTEGER,
    project_guid TEXT,
    project_name TEXT,
    city TEXT,
    target_amount DECIMAL(15,2),
    actual_amount DECIMAL(15,2),
    achievement_rate DECIMAL(5,2),
    contract_count INTEGER,
    area DECIMAL(10,2),
    unit_price DECIMAL(12,2),
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ads_group_sales_date ON ads_group_sales_report(report_date);
CREATE INDEX IF NOT EXISTS idx_ads_group_sales_project ON ads_group_sales_report(project_guid);

-- 4.2 Ads_group_salesdate_report 集团签约回款周月年报
CREATE TABLE IF NOT EXISTS ads_group_salesdate_report (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type TEXT,
    report_year INTEGER,
    report_week INTEGER,
    report_month INTEGER,
    project_guid TEXT,
    project_name TEXT,
    contract_amount DECIMAL(15,2),
    payment_amount DECIMAL(15,2),
    payment_rate DECIMAL(5,2),
    contract_count INTEGER,
    payment_count INTEGER,
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ads_group_date_type ON ads_group_salesdate_report(report_type);
CREATE INDEX IF NOT EXISTS idx_ads_group_date_project ON ads_group_salesdate_report(project_guid);

-- 4.3 Ads_group_pay_report 集团费用支出汇总表
CREATE TABLE IF NOT EXISTS ads_group_pay_report (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE,
    year INTEGER,
    month INTEGER,
    project_guid TEXT,
    project_name TEXT,
    contract_pay_amount DECIMAL(15,2),
    fee_amount DECIMAL(15,2),
    total_amount DECIMAL(15,2),
    budget_amount DECIMAL(15,2),
    variance_amount DECIMAL(15,2),
    variance_rate DECIMAL(5,2),
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ads_group_pay_date ON ads_group_pay_report(report_date);
CREATE INDEX IF NOT EXISTS idx_ads_group_pay_project ON ads_group_pay_report(project_guid);

-- 4.4 Ads_project_cost_report 项目成本费用报表
CREATE TABLE IF NOT EXISTS ads_project_cost_report (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE,
    year INTEGER,
    month INTEGER,
    project_guid TEXT,
    project_name TEXT,
    account_number TEXT,
    account_name TEXT,
    cost_type TEXT,
    budget_amount DECIMAL(15,2),
    actual_amount DECIMAL(15,2),
    variance_amount DECIMAL(15,2),
    variance_rate DECIMAL(5,2),
    completion_rate DECIMAL(5,2),
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ads_project_cost_date ON ads_project_cost_report(report_date);
CREATE INDEX IF NOT EXISTS idx_ads_project_cost_project ON ads_project_cost_report(project_guid);
CREATE INDEX IF NOT EXISTS idx_ads_project_cost_account ON ads_project_cost_report(account_number);

-- 4.5 Ads_sales_dashboard 营销驾驶舱大屏
CREATE TABLE IF NOT EXISTS ads_sales_dashboard (
    dashboard_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dashboard_date DATE,
    project_guid TEXT,
    project_name TEXT,
    total_units INTEGER,
    sold_units INTEGER,
    available_units INTEGER,
    sell_through_rate DECIMAL(5,2),
    total_sales DECIMAL(15,2),
    total_payment DECIMAL(15,2),
    payment_rate DECIMAL(5,2),
    avg_unit_price DECIMAL(12,2),
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ads_sales_dash_date ON ads_sales_dashboard(dashboard_date);
CREATE INDEX IF NOT EXISTS idx_ads_sales_dash_project ON ads_sales_dashboard(project_guid);

-- 4.6 Ads_finance_dashboard 财务驾驶舱大屏
CREATE TABLE IF NOT EXISTS ads_finance_dashboard (
    dashboard_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dashboard_date DATE,
    company_code TEXT,
    total_revenue DECIMAL(15,2),
    total_cost DECIMAL(15,2),
    total_profit DECIMAL(15,2),
    profit_margin DECIMAL(5,2),
    total_assets DECIMAL(15,2),
    total_liabilities DECIMAL(15,2),
    cash_flow DECIMAL(15,2),
    budget_execution_rate DECIMAL(5,2),
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ads_finance_dash_date ON ads_finance_dashboard(dashboard_date);
CREATE INDEX IF NOT EXISTS idx_ads_finance_dash_company ON ads_finance_dashboard(company_code);

-- 4.7 Ads_szl_dashboard 收支利大屏
CREATE TABLE IF NOT EXISTS ads_szl_dashboard (
    dashboard_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dashboard_date DATE,
    project_guid TEXT,
    project_name TEXT,
    sales_revenue DECIMAL(15,2),
    total_cost DECIMAL(15,2),
    total_expense DECIMAL(15,2),
    operating_profit DECIMAL(15,2),
    net_profit DECIMAL(15,2),
    profit_margin DECIMAL(5,2),
    roi DECIMAL(5,2),
    data_version DATE,
    created_time DATETIME
);

CREATE INDEX IF NOT EXISTS idx_ads_szl_dash_date ON ads_szl_dashboard(dashboard_date);
CREATE INDEX IF NOT EXISTS idx_ads_szl_dash_project ON ads_szl_dashboard(project_guid);

-- ============================================
-- 权限控制表（论文 5.2 节）
-- ============================================

CREATE TABLE IF NOT EXISTS dim_permission (
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    role_id TEXT,
    department_id TEXT,
    project_guid TEXT,
    permission_key TEXT,
    data_scope TEXT,
    is_active INTEGER DEFAULT 1,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_permission_user ON dim_permission(user_id);
CREATE INDEX IF NOT EXISTS idx_permission_project ON dim_permission(project_guid);

-- ============================================
-- 指标口径库（论文 3.2 节）
-- ============================================

CREATE TABLE IF NOT EXISTS dim_indicator (
    indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_code TEXT UNIQUE,
    indicator_name TEXT,
    calculation_rule TEXT,
    formula TEXT,
    unit TEXT,
    version TEXT,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_indicator_code ON dim_indicator(indicator_code);

-- 插入核心指标定义
INSERT INTO dim_indicator (indicator_code, indicator_name, calculation_rule, formula, unit, version) VALUES
('IND001', '销售去化率', '已售房源数/总房源数*100%', 'sold_units/total_units*100', '%', 'v1.0'),
('IND002', '项目回款率', '已回款金额/应收回款金额*100%', 'payment_amount/receivable_amount*100', '%', 'v1.0'),
('IND003', '合同执行率', '已执行合同金额/合同总金额*100%', 'executed_amount/contract_amount*100', '%', 'v1.0'),
('IND004', '预算执行率', '实际支出/预算金额*100%', 'actual_amount/budget_amount*100', '%', 'v1.0'),
('IND005', '销售目标达成率', '实际销售额/目标销售额*100%', 'actual_sales/target_sales*100', '%', 'v1.0'),
('IND006', '毛利率', '(销售收入 - 销售成本)/销售收入*100%', '(revenue-cost)/revenue*100', '%', 'v1.0');

-- ============================================
-- 验证表创建
-- ============================================

SELECT 'ODS 层' as layer, COUNT(*) as table_count FROM sqlite_master WHERE type='table' AND name LIKE 'ods_%'
UNION ALL
SELECT 'DWD 层', COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'dwd_%'
UNION ALL
SELECT 'DWS 层', COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'dws_%'
UNION ALL
SELECT 'ADS 层', COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'ads_%'
UNION ALL
SELECT '维度表', COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'dim_%';
