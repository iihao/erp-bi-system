-- 地产行业 ERP 商业智能报表系统数据库表设计
-- 基于论文设计 + 行业最佳实践
-- 创建时间：2026-03-18

-- ============================================
-- 1. 基础数据模块
-- ============================================

-- 1.1 项目信息表
CREATE TABLE IF NOT EXISTS re_projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code TEXT NOT NULL UNIQUE,
    project_name TEXT NOT NULL,
    city TEXT NOT NULL,
    district TEXT,
    address TEXT,
    project_type TEXT,
    total_area DECIMAL(15,2),
    total_units INTEGER,
    total_investment DECIMAL(15,2),
    start_date DATE,
    expected_completion DATE,
    actual_completion DATE,
    project_status TEXT DEFAULT 'planning',
    developer TEXT,
    property_management TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_project_city ON re_projects(city);
CREATE INDEX IF NOT EXISTS idx_project_status ON re_projects(project_status);

-- 1.2 楼栋信息表
CREATE TABLE IF NOT EXISTS re_buildings (
    building_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    building_code TEXT NOT NULL,
    building_name TEXT NOT NULL,
    building_type TEXT,
    floor_count INTEGER,
    unit_count INTEGER,
    total_area DECIMAL(15,2),
    completion_date DATE,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES re_projects(project_id)
);

CREATE INDEX IF NOT EXISTS idx_building_project ON re_buildings(project_id);

-- 1.3 房源/单元信息表
CREATE TABLE IF NOT EXISTS re_units (
    unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id INTEGER NOT NULL,
    unit_code TEXT NOT NULL,
    unit_name TEXT NOT NULL,
    floor INTEGER,
    unit_number INTEGER,
    unit_type TEXT,
    building_area DECIMAL(10,2),
    internal_area DECIMAL(10,2),
    share_area DECIMAL(10,2),
    orientation TEXT,
    total_price DECIMAL(15,2),
    unit_price DECIMAL(12,2),
    unit_status TEXT DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (building_id) REFERENCES re_buildings(building_id)
);

CREATE INDEX IF NOT EXISTS idx_unit_building ON re_units(building_id);
CREATE INDEX IF NOT EXISTS idx_unit_status ON re_units(unit_status);
CREATE INDEX IF NOT EXISTS idx_unit_type ON re_units(unit_type);

-- ============================================
-- 2. 客户管理模块
-- ============================================

-- 2.1 客户信息表
CREATE TABLE IF NOT EXISTS re_customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    customer_type TEXT DEFAULT 'personal',
    id_type TEXT,
    id_number TEXT,
    gender TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    source TEXT,
    intention_level TEXT,
    follow_count INTEGER DEFAULT 0,
    last_follow_date DATE,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customer_phone ON re_customers(phone);
CREATE INDEX IF NOT EXISTS idx_customer_source ON re_customers(source);
CREATE INDEX IF NOT EXISTS idx_customer_status ON re_customers(status);

-- 2.2 客户跟进记录表
CREATE TABLE IF NOT EXISTS re_customer_followups (
    followup_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    sales_id INTEGER,
    followup_date DATETIME NOT NULL,
    followup_type TEXT,
    followup_content TEXT,
    customer_feedback TEXT,
    next_plan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES re_customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_followup_customer ON re_customer_followups(customer_id);
CREATE INDEX IF NOT EXISTS idx_followup_date ON re_customer_followups(followup_date);

-- ============================================
-- 3. 销售管理模块
-- ============================================

-- 3.1 认购书表
CREATE TABLE IF NOT EXISTS re_subscriptions (
    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_code TEXT NOT NULL UNIQUE,
    unit_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    sales_id INTEGER,
    subscription_date DATE NOT NULL,
    total_price DECIMAL(15,2) NOT NULL,
    deposit_amount DECIMAL(15,2) NOT NULL,
    payment_plan TEXT,
    mortgage_bank TEXT,
    mortgage_amount DECIMAL(15,2),
    mortgage_period INTEGER,
    contract_deadline DATE,
    subscription_status TEXT DEFAULT 'active',
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES re_units(unit_id),
    FOREIGN KEY (customer_id) REFERENCES re_customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_subscription_unit ON re_subscriptions(unit_id);
CREATE INDEX IF NOT EXISTS idx_subscription_customer ON re_subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_subscription_date ON re_subscriptions(subscription_date);
CREATE INDEX IF NOT EXISTS idx_subscription_status ON re_subscriptions(subscription_status);

-- 3.2 销售合同表
CREATE TABLE IF NOT EXISTS re_contracts (
    contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_code TEXT NOT NULL UNIQUE,
    subscription_id INTEGER,
    unit_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    contract_date DATE NOT NULL,
    contract_type TEXT DEFAULT 'new_sale',
    total_price DECIMAL(15,2) NOT NULL,
    area DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    payment_method TEXT NOT NULL,
    total_paid DECIMAL(15,2) DEFAULT 0,
    balance DECIMAL(15,2) DEFAULT 0,
    mortgage_amount DECIMAL(15,2),
    mortgage_status TEXT,
    delivery_date DATE,
    contract_status TEXT DEFAULT 'active',
    signed_date DATE,
    filed_date DATE,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES re_subscriptions(subscription_id),
    FOREIGN KEY (unit_id) REFERENCES re_units(unit_id),
    FOREIGN KEY (customer_id) REFERENCES re_customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_contract_unit ON re_contracts(unit_id);
CREATE INDEX IF NOT EXISTS idx_contract_customer ON re_contracts(customer_id);
CREATE INDEX IF NOT EXISTS idx_contract_date ON re_contracts(contract_date);
CREATE INDEX IF NOT EXISTS idx_contract_status ON re_contracts(contract_status);

-- 3.3 收款记录表
CREATE TABLE IF NOT EXISTS re_payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_code TEXT NOT NULL UNIQUE,
    contract_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    payment_date DATE NOT NULL,
    payment_type TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    payment_method TEXT NOT NULL,
    bank_account TEXT,
    invoice_number TEXT,
    invoice_date DATE,
    remarks TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES re_contracts(contract_id),
    FOREIGN KEY (customer_id) REFERENCES re_customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_payment_contract ON re_payments(contract_id);
CREATE INDEX IF NOT EXISTS idx_payment_customer ON re_payments(customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_date ON re_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_payment_type ON re_payments(payment_type);

-- ============================================
-- 4. 财务管理模块
-- ============================================

-- 4.1 应收款项表
CREATE TABLE IF NOT EXISTS re_receivables (
    receivable_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    receivable_type TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    due_date DATE NOT NULL,
    received_amount DECIMAL(15,2) DEFAULT 0,
    balance DECIMAL(15,2) DEFAULT 0,
    overdue_days INTEGER DEFAULT 0,
    penalty_amount DECIMAL(15,2) DEFAULT 0,
    status TEXT DEFAULT 'pending',
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES re_contracts(contract_id),
    FOREIGN KEY (customer_id) REFERENCES re_customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_receivable_contract ON re_receivables(contract_id);
CREATE INDEX IF NOT EXISTS idx_receivable_status ON re_receivables(status);
CREATE INDEX IF NOT EXISTS idx_receivable_due_date ON re_receivables(due_date);

-- 4.2 退款记录表
CREATE TABLE IF NOT EXISTS re_refunds (
    refund_id INTEGER PRIMARY KEY AUTOINCREMENT,
    refund_code TEXT NOT NULL UNIQUE,
    contract_id INTEGER,
    customer_id INTEGER NOT NULL,
    payment_id INTEGER,
    refund_amount DECIMAL(15,2) NOT NULL,
    refund_type TEXT NOT NULL,
    refund_reason TEXT NOT NULL,
    apply_date DATE NOT NULL,
    approve_date DATE,
    refund_date DATE,
    refund_status TEXT DEFAULT 'pending',
    approved_by INTEGER,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES re_contracts(contract_id),
    FOREIGN KEY (customer_id) REFERENCES re_customers(customer_id),
    FOREIGN KEY (payment_id) REFERENCES re_payments(payment_id)
);

CREATE INDEX IF NOT EXISTS idx_refund_contract ON re_refunds(contract_id);
CREATE INDEX IF NOT EXISTS idx_refund_status ON re_refunds(refund_status);

-- ============================================
-- 5. 统计分析视图
-- ============================================

-- 5.1 销售日报视图
CREATE VIEW IF NOT EXISTS v_daily_sales_report AS
SELECT 
    DATE(c.contract_date) as report_date,
    p.project_name,
    p.city,
    COUNT(DISTINCT c.contract_id) as contract_count,
    COUNT(DISTINCT c.customer_id) as customer_count,
    SUM(c.total_price) as total_sales,
    SUM(c.area) as total_area,
    AVG(c.unit_price) as avg_unit_price,
    SUM(pay.total_paid) as total_received
FROM re_contracts c
LEFT JOIN re_units u ON c.unit_id = u.unit_id
LEFT JOIN re_buildings b ON u.building_id = b.building_id
LEFT JOIN re_projects p ON b.project_id = p.project_id
LEFT JOIN (
    SELECT contract_id, SUM(amount) as total_paid 
    FROM re_payments 
    GROUP BY contract_id
) pay ON c.contract_id = pay.contract_id
WHERE c.contract_status != 'cancelled'
GROUP BY DATE(c.contract_date), p.project_id, p.project_name, p.city
ORDER BY report_date DESC;

-- 5.2 销售业绩统计视图
CREATE VIEW IF NOT EXISTS v_sales_performance AS
SELECT 
    p.project_name,
    COUNT(DISTINCT u.unit_id) as total_units,
    COUNT(DISTINCT CASE WHEN u.unit_status = 'signed' THEN u.unit_id END) as sold_units,
    COUNT(DISTINCT CASE WHEN u.unit_status = 'available' THEN u.unit_id END) as available_units,
    SUM(CASE WHEN u.unit_status = 'signed' THEN u.total_price ELSE 0 END) as total_sales,
    ROUND(
        COUNT(DISTINCT CASE WHEN u.unit_status = 'signed' THEN u.unit_id END) * 100.0 / 
        NULLIF(COUNT(DISTINCT u.unit_id), 0), 2
    ) as sell_through_rate
FROM re_projects p
LEFT JOIN re_buildings b ON p.project_id = b.project_id
LEFT JOIN re_units u ON b.building_id = u.building_id
GROUP BY p.project_id, p.project_name;

-- 5.3 回款统计视图
CREATE VIEW IF NOT EXISTS v_collection_report AS
SELECT 
    p.project_name,
    COUNT(DISTINCT r.receivable_id) as total_receivables,
    SUM(r.amount) as total_amount,
    SUM(r.received_amount) as total_received,
    SUM(r.balance) as total_balance,
    ROUND(
        SUM(r.received_amount) * 100.0 / NULLIF(SUM(r.amount), 0), 2
    ) as collection_rate,
    SUM(CASE WHEN r.status = 'overdue' THEN r.balance ELSE 0 END) as overdue_amount,
    COUNT(DISTINCT CASE WHEN r.status = 'overdue' THEN r.receivable_id END) as overdue_count
FROM re_receivables r
LEFT JOIN re_contracts c ON r.contract_id = c.contract_id
LEFT JOIN re_units u ON c.unit_id = u.unit_id
LEFT JOIN re_buildings b ON u.building_id = b.building_id
LEFT JOIN re_projects p ON b.project_id = p.project_id
GROUP BY p.project_id, p.project_name;

-- ============================================
-- 插入仿真测试数据
-- ============================================

-- 插入项目数据
INSERT INTO re_projects (project_code, project_name, city, district, address, project_type, total_area, total_units, total_investment, start_date, expected_completion, project_status, developer) VALUES
('PRJ001', '绿洲花园', '上海', '浦东新区', '世纪大道 1000 号', '住宅', 150000.00, 1200, 800000000, '2023-03-01', '2025-12-31', 'construction', '绿洲地产集团'),
('PRJ002', '金融中心', '上海', '陆家嘴', '银城中路 500 号', '商业', 200000.00, 500, 1500000000, '2022-06-01', '2025-06-30', 'construction', '绿洲地产集团'),
('PRJ003', '阳光城', '杭州', '西湖区', '文一路 888 号', '住宅', 120000.00, 980, 650000000, '2023-09-01', '2026-03-31', 'planning', '绿洲地产集团'),
('PRJ004', '翡翠湾', '苏州', '工业园区', '金鸡湖大道 666 号', '综合体', 180000.00, 1500, 1200000000, '2021-01-01', '2025-12-31', 'completed', '绿洲地产集团');

-- 插入楼栋数据
INSERT INTO re_buildings (project_id, building_code, building_name, building_type, floor_count, unit_count, total_area) VALUES
(1, 'B001', '1 号楼', '高层', 32, 128, 15000.00),
(1, 'B002', '2 号楼', '高层', 32, 128, 15000.00),
(1, 'B003', '3 号楼', '小高层', 18, 72, 9000.00),
(2, 'B004', 'A 座', '超高层', 58, 200, 50000.00),
(2, 'B005', 'B 座', '超高层', 58, 200, 50000.00),
(3, 'B006', '1 号楼', '高层', 28, 112, 13000.00),
(3, 'B007', '2 号楼', '高层', 28, 112, 13000.00),
(4, 'B008', '住宅 1 栋', '高层', 30, 120, 14000.00),
(4, 'B009', '商业 1 栋', '商业', 5, 50, 8000.00);

-- 插入房源数据
INSERT INTO re_units (building_id, unit_code, unit_name, floor, unit_number, unit_type, building_area, internal_area, unit_price, total_price, unit_status) VALUES
-- 绿洲花园 1 号楼
(1, 'U001001', '1-1001', 10, 1, '3 室 2 厅', 120.00, 95.00, 65000.00, 7800000.00, 'available'),
(1, 'U001002', '1-1002', 10, 2, '2 室 2 厅', 90.00, 72.00, 68000.00, 6120000.00, 'reserved'),
(1, 'U001003', '1-1101', 11, 1, '3 室 2 厅', 120.00, 95.00, 66000.00, 7920000.00, 'signed'),
(1, 'U001004', '1-1102', 11, 2, '2 室 2 厅', 90.00, 72.00, 69000.00, 6210000.00, 'available'),
(1, 'U001005', '1-1201', 12, 1, '3 室 2 厅', 120.00, 95.00, 67000.00, 8040000.00, 'signed'),
(1, 'U001006', '1-1202', 12, 2, '4 室 2 厅', 140.00, 112.00, 70000.00, 9800000.00, 'available'),
-- 绿洲花园 2 号楼
(2, 'U002001', '2-1001', 10, 1, '3 室 2 厅', 125.00, 100.00, 64000.00, 8000000.00, 'available'),
(2, 'U002002', '2-1002', 10, 2, '2 室 2 厅', 88.00, 70.00, 67000.00, 5896000.00, 'signed'),
(2, 'U002003', '2-1501', 15, 1, '3 室 2 厅', 125.00, 100.00, 68000.00, 8500000.00, 'signed'),
(2, 'U002004', '2-1502', 15, 2, '2 室 2 厅', 88.00, 70.00, 70000.00, 6160000.00, 'available'),
-- 金融中心 A 座
(4, 'U004001', 'A-2001', 20, 1, '写字楼', 200.00, 160.00, 80000.00, 16000000.00, 'available'),
(4, 'U004002', 'A-2002', 20, 2, '写字楼', 150.00, 120.00, 85000.00, 12750000.00, 'reserved'),
(4, 'U004003', 'A-3001', 30, 1, '写字楼', 300.00, 240.00, 90000.00, 27000000.00, 'signed'),
-- 翡翠湾住宅
(8, 'U008001', '1-801', 8, 1, '3 室 2 厅', 118.00, 94.00, 45000.00, 5310000.00, 'delivered'),
(8, 'U008002', '1-802', 8, 2, '2 室 2 厅', 85.00, 68.00, 48000.00, 4080000.00, 'delivered'),
(8, 'U008003', '1-901', 9, 1, '3 室 2 厅', 118.00, 94.00, 46000.00, 5428000.00, 'delivered'),
(8, 'U008004', '1-902', 9, 2, '4 室 2 厅', 135.00, 108.00, 50000.00, 6750000.00, 'available');

-- 插入客户数据
INSERT INTO re_customers (customer_code, customer_name, customer_type, id_type, id_number, phone, city, source, intention_level, status) VALUES
('CUST001', '张三', 'personal', 'id_card', '310101199001011234', '13800138001', '上海', 'walk_in', 'A', 'active'),
('CUST002', '李四', 'personal', 'id_card', '310101198505055678', '13800138002', '上海', 'referral', 'A', 'active'),
('CUST003', '王五', 'personal', 'id_card', '330101199203032345', '13800138003', '杭州', 'online', 'B', 'active'),
('CUST004', '赵六', 'personal', 'id_card', '320501198808086789', '13800138004', '苏州', 'walk_in', 'A', 'active'),
('CUST005', '钱七', 'personal', 'id_card', '310101199512123456', '13800138005', '上海', 'advertisement', 'C', 'active'),
('CUST006', '上海科技有限公司', 'company', 'business_license', '91310000MA1234567X', '13800138006', '上海', 'referral', 'A', 'active'),
('CUST007', '周八', 'personal', 'id_card', '310101199107074567', '13800138007', '上海', 'walk_in', 'B', 'active'),
('CUST008', '吴九', 'personal', 'id_card', '330101199309098901', '13800138008', '杭州', 'online', 'A', 'active');

-- 插入认购书数据
INSERT INTO re_subscriptions (subscription_code, unit_id, customer_id, subscription_date, total_price, deposit_amount, payment_plan, subscription_status) VALUES
('SUB202603001', 3, 1, '2026-03-01', 7920000.00, 200000.00, '按揭', 'signed'),
('SUB202603002', 5, 2, '2026-03-05', 8040000.00, 200000.00, '按揭', 'signed'),
('SUB202603003', 8, 3, '2026-03-08', 5896000.00, 150000.00, '按揭', 'signed'),
('SUB202603004', 9, 4, '2026-03-10', 8500000.00, 200000.00, '一次性', 'signed'),
('SUB202603005', 13, 6, '2026-03-12', 27000000.00, 500000.00, '按揭', 'signed'),
('SUB202603006', 2, 5, '2026-03-15', 6120000.00, 150000.00, '按揭', 'active');

-- 插入销售合同数据
INSERT INTO re_contracts (contract_code, subscription_id, unit_id, customer_id, contract_date, total_price, area, unit_price, payment_method, total_paid, mortgage_amount, contract_status) VALUES
('CNT202603001', 1, 3, 1, '2026-03-05', 7920000.00, 120.00, 66000.00, '按揭', 2376000.00, 5544000.00, 'active'),
('CNT202603002', 2, 5, 2, '2026-03-08', 8040000.00, 120.00, 67000.00, '按揭', 2412000.00, 5628000.00, 'active'),
('CNT202603003', 3, 8, 3, '2026-03-12', 5896000.00, 88.00, 67000.00, '按揭', 1768800.00, 4127200.00, 'active'),
('CNT202603004', 4, 9, 4, '2026-03-15', 8500000.00, 125.00, 68000.00, '一次性', 8500000.00, 0.00, 'active'),
('CNT202603005', 5, 13, 6, '2026-03-18', 27000000.00, 300.00, 90000.00, '按揭', 8100000.00, 18900000.00, 'active');

-- 插入收款记录数据
INSERT INTO re_payments (payment_code, contract_id, customer_id, payment_date, payment_type, amount, payment_method, remarks) VALUES
('PAY202603001', 1, 1, '2026-03-05', 'down_payment', 2376000.00, 'transfer', '首付款 30%'),
('PAY202603002', 2, 2, '2026-03-08', 'down_payment', 2412000.00, 'transfer', '首付款 30%'),
('PAY202603003', 3, 3, '2026-03-12', 'down_payment', 1768800.00, 'transfer', '首付款 30%'),
('PAY202603004', 4, 4, '2026-03-15', 'down_payment', 8500000.00, 'transfer', '一次性付款'),
('PAY202603005', 5, 6, '2026-03-18', 'down_payment', 8100000.00, 'transfer', '首付款 30%'),
('PAY202603006', 1, 1, '2026-03-10', 'deposit', 200000.00, 'pos', '认购定金'),
('PAY202603007', 2, 2, '2026-03-06', 'deposit', 200000.00, 'pos', '认购定金');

-- 插入应收款项数据
INSERT INTO re_receivables (contract_id, customer_id, receivable_type, amount, due_date, received_amount, status) VALUES
(1, 1, 'down_payment', 2376000.00, '2026-03-05', 2376000.00, 'paid'),
(1, 1, 'mortgage', 5544000.00, '2026-04-05', 0.00, 'pending'),
(2, 2, 'down_payment', 2412000.00, '2026-03-08', 2412000.00, 'paid'),
(2, 2, 'mortgage', 5628000.00, '2026-04-08', 0.00, 'pending'),
(3, 3, 'down_payment', 1768800.00, '2026-03-12', 1768800.00, 'paid'),
(3, 3, 'mortgage', 4127200.00, '2026-04-12', 0.00, 'pending'),
(4, 4, 'down_payment', 8500000.00, '2026-03-15', 8500000.00, 'paid'),
(5, 6, 'down_payment', 8100000.00, '2026-03-18', 8100000.00, 'paid'),
(5, 6, 'mortgage', 18900000.00, '2026-04-18', 0.00, 'pending');

-- 插入客户跟进记录
INSERT INTO re_customer_followups (customer_id, followup_date, followup_type, followup_content, customer_feedback) VALUES
(1, '2026-03-01 10:00:00', 'visit', '客户首次到访，参观样板间', '对 3 房户型比较满意，考虑中'),
(1, '2026-03-03 15:00:00', 'phone', '电话回访，询问购房意向', '表示需要考虑贷款问题'),
(1, '2026-03-05 09:00:00', 'visit', '客户二次到访，确定购买意向', '决定购买 1-1101，准备签约'),
(2, '2026-03-04 14:00:00', 'wechat', '微信沟通，介绍项目优势', '对地段和配套比较认可'),
(2, '2026-03-06 10:00:00', 'visit', '客户带家人复看', '家人满意，决定认购'),
(3, '2026-03-07 16:00:00', 'phone', '网络咨询后电话跟进', '外地客户，计划来上海看房'),
(3, '2026-03-08 11:00:00', 'visit', '客户从杭州来沪看房', '当天认购 2-1002');

-- ============================================
-- 验证数据
-- ============================================

SELECT '项目总数' as item, COUNT(*) as count FROM re_projects
UNION ALL
SELECT '楼栋总数', COUNT(*) FROM re_buildings
UNION ALL
SELECT '房源总数', COUNT(*) FROM re_units
UNION ALL
SELECT '客户总数', COUNT(*) FROM re_customers
UNION ALL
SELECT '认购书总数', COUNT(*) FROM re_subscriptions
UNION ALL
SELECT '合同总数', COUNT(*) FROM re_contracts
UNION ALL
SELECT '收款记录总数', COUNT(*) FROM re_payments
UNION ALL
SELECT '应收款项总数', COUNT(*) FROM re_receivables;
