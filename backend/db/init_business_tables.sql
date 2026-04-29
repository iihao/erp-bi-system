-- ============================================================
-- AI数据融合 业务表初始化脚本 (SQLite 版本)
-- ============================================================

-- 产品表
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code VARCHAR(30) NOT NULL UNIQUE,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    unit_price DECIMAL(10,2) DEFAULT 0.00,
    stock_quantity INT DEFAULT 0,
    status TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 客户表
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code VARCHAR(20) NOT NULL UNIQUE,
    customer_name VARCHAR(100) NOT NULL,
    customer_type VARCHAR(20),
    industry VARCHAR(50),
    contact_person VARCHAR(50),
    contact_phone VARCHAR(20),
    status TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 销售订单表
CREATE TABLE IF NOT EXISTS sales_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no VARCHAR(30) NOT NULL UNIQUE,
    customer_id INT,
    order_date DATE,
    final_amount DECIMAL(12,2) DEFAULT 0.00,
    order_status VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- 订单明细表
CREATE TABLE IF NOT EXISTS sales_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INT,
    product_id INT,
    quantity INT DEFAULT 0,
    unit_price DECIMAL(10,2) DEFAULT 0.00,
    subtotal DECIMAL(12,2) DEFAULT 0.00,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES sales_orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 供应商表
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_code VARCHAR(20) NOT NULL UNIQUE,
    supplier_name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(50),
    contact_phone VARCHAR(20),
    status TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 插入模拟数据
-- ============================================================

-- 产品数据
INSERT OR IGNORE INTO products (product_code, product_name, category, unit_price, stock_quantity) VALUES
('P001', 'iPhone 15 Pro', '手机', 8999.00, 100),
('P002', 'MacBook Pro 14', '笔记本', 14999.00, 50),
('P003', 'iPad Air', '平板', 4799.00, 80),
('P004', 'AirPods Pro', '耳机', 1899.00, 200),
('P005', 'Apple Watch', '手表', 3199.00, 150),
('P006', '华为 Mate60 Pro', '手机', 6999.00, 120),
('P007', '小米 14 Ultra', '手机', 5999.00, 180),
('P008', '联想 ThinkPad X1', '笔记本', 12999.00, 40),
('P009', '戴尔 XPS 15', '笔记本', 11999.00, 60),
('P010', '索尼 WH-1000XM5', '耳机', 2499.00, 100);

-- 客户数据
INSERT OR IGNORE INTO customers (customer_code, customer_name, customer_type, industry) VALUES
('C001', '张三', '个人', 'IT'),
('C002', '李四', '个人', '金融'),
('C003', '王五', '个人', '教育'),
('C004', '赵六', '个人', '医疗'),
('C005', '北京科技有限公司', '企业', 'IT'),
('C006', '上海贸易公司', '企业', '贸易'),
('C007', '广州制造厂', '企业', '制造'),
('C008', '深圳电子公司', '企业', '电子'),
('C009', '杭州网络公司', '企业', '互联网'),
('C010', '成都软件公司', '企业', '软件');

-- 销售订单数据
INSERT OR IGNORE INTO sales_orders (order_no, customer_id, order_date, final_amount, order_status) VALUES
('SO202503001', 1, '2025-03-01', 8999.00, 'completed'),
('SO202503002', 2, '2025-03-05', 14999.00, 'completed'),
('SO202503003', 3, '2025-03-10', 4799.00, 'completed'),
('SO202503004', 4, '2025-03-15', 3798.00, 'completed'),
('SO202503005', 5, '2025-03-20', 44995.00, 'completed'),
('SO202503006', 6, '2025-03-22', 35997.00, 'completed'),
('SO202503007', 7, '2025-03-25', 23998.00, 'completed'),
('SO202503008', 8, '2025-03-27', 51996.00, 'completed'),
('SO202503009', 9, '2025-03-28', 11999.00, 'completed'),
('SO202503010', 10, '2025-03-30', 24990.00, 'completed');

-- 订单明细数据
INSERT OR IGNORE INTO sales_order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
(1, 1, 1, 8999.00, 8999.00),
(2, 2, 1, 14999.00, 14999.00),
(3, 3, 1, 4799.00, 4799.00),
(4, 4, 2, 1899.00, 3798.00),
(5, 2, 3, 14999.00, 44997.00),
(6, 1, 4, 8999.00, 35996.00),
(7, 6, 2, 6999.00, 13998.00),
(7, 7, 1, 5999.00, 5999.00),
(7, 4, 2, 1899.00, 3798.00),
(8, 8, 2, 12999.00, 25998.00),
(8, 9, 2, 11999.00, 23998.00),
(8, 10, 1, 2499.00, 2499.00),
(9, 9, 1, 11999.00, 11999.00),
(10, 10, 10, 2499.00, 24990.00);

-- 供应商数据
INSERT OR IGNORE INTO suppliers (supplier_code, supplier_name, contact_person, contact_phone) VALUES
('S001', '苹果中国', '李明', '400-666-8800'),
('S002', '华为技术', '王芳', '400-830-8300'),
('S003', '小米科技', '张强', '400-100-5678'),
('S004', '联想集团', '赵敏', '400-990-8888'),
('S005', '戴尔中国', '刘伟', '400-886-8610'),
('S006', '索尼电子', '陈静', '400-810-9000'),
('S007', '三星电子', '杨帆', '400-810-5858'),
('S008', 'OPPO 广东', '周杰', '400-166-6888'),
('S009', 'VIVO 移动', '吴磊', '400-678-9688'),
('S010', '荣耀终端', '郑华', '400-830-8500');
