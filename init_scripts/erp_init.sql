-- ============================================================
-- AI数据融合平台 MySQL 初始化脚本
-- 包含：ERP 业务表 + 模拟数据 + 数仓分层表
-- ============================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS erp_source DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS erp_ods DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS erp_dwd DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS erp_dws DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS erp_ads DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE erp_source;

-- ============================================================
-- 1. ERP 业务表 - 原始业务系统表
-- ============================================================

-- 1.1 供应商表
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_code VARCHAR(20) NOT NULL UNIQUE,
    supplier_name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(50),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    address VARCHAR(255),
    city VARCHAR(50),
    province VARCHAR(50),
    credit_level VARCHAR(10),
    status TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_supplier_code (supplier_code),
    INDEX idx_supplier_name (supplier_name),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='供应商表';

-- 1.2 商品分类表
CREATE TABLE IF NOT EXISTS categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_code VARCHAR(20) NOT NULL UNIQUE,
    category_name VARCHAR(100) NOT NULL,
    parent_id INT DEFAULT 0,
    level TINYINT DEFAULT 1,
    sort_order INT DEFAULT 0,
    status TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category_code (category_code),
    INDEX idx_parent_id (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类表';

-- 1.3 商品表
CREATE TABLE IF NOT EXISTS products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_code VARCHAR(30) NOT NULL UNIQUE,
    product_name VARCHAR(200) NOT NULL,
    category_id INT,
    brand VARCHAR(100),
    model VARCHAR(100),
    unit VARCHAR(20),
    cost_price DECIMAL(10,2) DEFAULT 0.00,
    selling_price DECIMAL(10,2) DEFAULT 0.00,
    min_stock INT DEFAULT 0,
    max_stock INT DEFAULT 0,
    weight DECIMAL(10,3),
    length DECIMAL(10,2),
    width DECIMAL(10,2),
    height DECIMAL(10,2),
    status TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    INDEX idx_product_code (product_code),
    INDEX idx_product_name (product_name),
    INDEX idx_category_id (category_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';

-- 1.4 仓库表
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id INT PRIMARY KEY AUTO_INCREMENT,
    warehouse_code VARCHAR(20) NOT NULL UNIQUE,
    warehouse_name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(50),
    province VARCHAR(50),
    manager VARCHAR(50),
    manager_phone VARCHAR(20),
    capacity DECIMAL(12,2),
    status TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_warehouse_code (warehouse_code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='仓库表';

-- 1.5 库存表
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id INT PRIMARY KEY AUTO_INCREMENT,
    warehouse_id INT,
    product_id INT,
    quantity INT DEFAULT 0,
    locked_quantity INT DEFAULT 0,
    available_quantity INT GENERATED ALWAYS AS (quantity - locked_quantity) STORED,
    last_stock_check DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    UNIQUE KEY uk_warehouse_product (warehouse_id, product_id),
    INDEX idx_product_id (product_id),
    INDEX idx_warehouse_id (warehouse_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存表';

-- 1.6 客户表
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_code VARCHAR(20) NOT NULL UNIQUE,
    customer_name VARCHAR(100) NOT NULL,
    customer_type VARCHAR(20) DEFAULT 'retail',
    contact_person VARCHAR(50),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    address VARCHAR(255),
    city VARCHAR(50),
    province VARCHAR(50),
    credit_limit DECIMAL(12,2) DEFAULT 0.00,
    credit_level VARCHAR(10),
    status TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer_code (customer_code),
    INDEX idx_customer_name (customer_name),
    INDEX idx_customer_type (customer_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户表';

-- 1.7 采购订单主表
CREATE TABLE IF NOT EXISTS purchase_orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(30) NOT NULL UNIQUE,
    supplier_id INT,
    warehouse_id INT,
    order_date DATE NOT NULL,
    expected_date DATE,
    actual_date DATE,
    total_amount DECIMAL(12,2) DEFAULT 0.00,
    discount_amount DECIMAL(12,2) DEFAULT 0.00,
    tax_amount DECIMAL(12,2) DEFAULT 0.00,
    final_amount DECIMAL(12,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'pending',
    remarks TEXT,
    created_by INT,
    approved_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
    INDEX idx_order_no (order_no),
    INDEX idx_supplier_id (supplier_id),
    INDEX idx_order_date (order_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购订单主表';

-- 1.8 采购订单明细表
CREATE TABLE IF NOT EXISTS purchase_order_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    quantity INT NOT NULL,
    received_quantity INT DEFAULT 0,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    tax_rate DECIMAL(5,4) DEFAULT 0.1300,
    tax_amount DECIMAL(12,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES purchase_orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购订单明细表';

-- 1.9 销售订单主表
CREATE TABLE IF NOT EXISTS sales_orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(30) NOT NULL UNIQUE,
    customer_id INT,
    warehouse_id INT,
    order_date DATE NOT NULL,
    expected_date DATE,
    actual_date DATE,
    total_amount DECIMAL(12,2) DEFAULT 0.00,
    discount_amount DECIMAL(12,2) DEFAULT 0.00,
    tax_amount DECIMAL(12,2) DEFAULT 0.00,
    final_amount DECIMAL(12,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'pending',
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    payment_method VARCHAR(20),
    remarks TEXT,
    created_by INT,
    approved_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
    INDEX idx_order_no (order_no),
    INDEX idx_customer_id (customer_id),
    INDEX idx_order_date (order_date),
    INDEX idx_status (status),
    INDEX idx_payment_status (payment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售订单主表';

-- 1.10 销售订单明细表
CREATE TABLE IF NOT EXISTS sales_order_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    quantity INT NOT NULL,
    shipped_quantity INT DEFAULT 0,
    unit_price DECIMAL(10,2) NOT NULL,
    cost_price DECIMAL(10,2) DEFAULT 0.00,
    subtotal DECIMAL(12,2) NOT NULL,
    profit DECIMAL(12,2) GENERATED ALWAYS AS (subtotal - cost_price * quantity) STORED,
    tax_rate DECIMAL(5,4) DEFAULT 0.1300,
    tax_amount DECIMAL(12,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES sales_orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售订单明细表';

-- 1.11 采购入库表
CREATE TABLE IF NOT EXISTS purchase_inbound (
    inbound_id INT PRIMARY KEY AUTO_INCREMENT,
    inbound_no VARCHAR(30) NOT NULL UNIQUE,
    order_id INT,
    warehouse_id INT,
    supplier_id INT,
    inbound_date DATE NOT NULL,
    total_quantity INT DEFAULT 0,
    total_amount DECIMAL(12,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'pending',
    remarks TEXT,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES purchase_orders(order_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    INDEX idx_inbound_no (inbound_no),
    INDEX idx_order_id (order_id),
    INDEX idx_inbound_date (inbound_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购入库表';

-- 1.12 采购入库明细表
CREATE TABLE IF NOT EXISTS purchase_inbound_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    inbound_id INT,
    product_id INT,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    batch_no VARCHAR(50),
    production_date DATE,
    expiry_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (inbound_id) REFERENCES purchase_inbound(inbound_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_inbound_id (inbound_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购入库明细表';

-- 1.13 销售出库表
CREATE TABLE IF NOT EXISTS sales_outbound (
    outbound_id INT PRIMARY KEY AUTO_INCREMENT,
    outbound_no VARCHAR(30) NOT NULL UNIQUE,
    order_id INT,
    warehouse_id INT,
    customer_id INT,
    outbound_date DATE NOT NULL,
    total_quantity INT DEFAULT 0,
    total_amount DECIMAL(12,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'pending',
    shipping_method VARCHAR(50),
    shipping_no VARCHAR(100),
    remarks TEXT,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES sales_orders(order_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    INDEX idx_outbound_no (outbound_no),
    INDEX idx_order_id (order_id),
    INDEX idx_outbound_date (outbound_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售出库表';

-- 1.14 销售出库明细表
CREATE TABLE IF NOT EXISTS sales_outbound_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    outbound_id INT,
    product_id INT,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    batch_no VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outbound_id) REFERENCES sales_outbound(outbound_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_outbound_id (outbound_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售出库明细表';

-- 1.15 库存流水表
CREATE TABLE IF NOT EXISTS inventory_transaction (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    transaction_no VARCHAR(30) NOT NULL UNIQUE,
    warehouse_id INT,
    product_id INT,
    transaction_type VARCHAR(20) NOT NULL,
    quantity INT NOT NULL,
    before_quantity INT NOT NULL,
    after_quantity INT NOT NULL,
    reference_type VARCHAR(20),
    reference_id INT,
    remarks TEXT,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_transaction_no (transaction_no),
    INDEX idx_product_id (product_id),
    INDEX idx_warehouse_id (warehouse_id),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存流水表';

-- ============================================================
-- 2. 插入模拟数据
-- ============================================================

-- 2.1 插入供应商数据
INSERT INTO suppliers (supplier_code, supplier_name, contact_person, contact_phone, contact_email, address, city, province, credit_level, status) VALUES
('SUP001', '华为技术有限公司', '张三', '13800138001', 'zhangsan@huawei.com', '龙岗区坂田华为基地', '深圳', '广东', 'A', 1),
('SUP002', '小米科技有限责任公司', '李四', '13800138002', 'lisi@xiaomi.com', '海淀区清河中街', '北京', '北京', 'A', 1),
('SUP003', '海尔集团股份有限公司', '王五', '13800138003', 'wangwu@haier.com', '崂山区海尔路', '青岛', '山东', 'A', 1),
('SUP004', '美的集团股份有限公司', '赵六', '13800138004', 'zhaoliu@midea.com', '顺德区北滘镇', '佛山', '广东', 'B', 1),
('SUP005', '格力电器股份有限公司', '孙七', '13800138005', 'sunqi@gree.com', '香洲区前山金鸡路', '珠海', '广东', 'A', 1),
('SUP006', 'TCL 科技集团股份有限公司', '周八', '13800138006', 'zhouba@tcl.com', '仲恺高新区惠风三路', '惠州', '广东', 'B', 1),
('SUP007', '海信集团有限公司', '吴九', '13800138007', 'wujiu@hisense.com', '市南区东海西路', '青岛', '山东', 'B', 1),
('SUP008', '联想集团有限公司', '郑十', '13800138008', 'zhengshi@lenovo.com', '海淀区上地信息路', '北京', '北京', 'A', 1),
('SUP009', '华硕电脑股份有限公司', '钱十一', '13800138009', 'qianshiyi@asus.com', '南山区科技园', '深圳', '广东', 'C', 1),
('SUP010', '戴尔计算机公司', '刘十二', '13800138010', 'liushier@dell.com', '思明区软件园', '厦门', '福建', 'B', 1);

-- 2.2 插入商品分类数据
INSERT INTO categories (category_code, category_name, parent_id, level, sort_order, status) VALUES
('CAT001', '电子产品', 0, 1, 1, 1),
('CAT002', '家用电器', 0, 1, 2, 1),
('CAT003', '数码配件', 0, 1, 3, 1),
('CAT004', '手机通讯', 0, 1, 4, 1),
('CAT005', '电脑办公', 0, 1, 5, 1),
('CAT001001', '手机', 1, 2, 1, 1),
('CAT001002', '平板', 1, 2, 2, 1),
('CAT001003', '智能穿戴', 1, 2, 3, 1),
('CAT002001', '空调', 2, 2, 1, 1),
('CAT002002', '冰箱', 2, 2, 2, 1),
('CAT002003', '洗衣机', 2, 2, 3, 1),
('CAT002004', '电视', 2, 2, 4, 1),
('CAT003001', '充电器', 3, 2, 1, 1),
('CAT003002', '数据线', 3, 2, 2, 1),
('CAT003003', '保护壳', 3, 2, 3, 1),
('CAT004001', '智能手机', 4, 2, 1, 1),
('CAT004002', '功能手机', 4, 2, 2, 1),
('CAT005001', '笔记本电脑', 5, 2, 1, 1),
('CAT005002', '台式机', 5, 2, 2, 1),
('CAT005003', '平板电脑', 5, 2, 3, 1);

-- 2.3 插入商品数据
INSERT INTO products (product_code, product_name, category_id, brand, model, unit, cost_price, selling_price, min_stock, max_stock, weight, status) VALUES
('P001', '华为 Mate 60 Pro', 6, '华为', 'Mate 60 Pro', '台', 5499.00, 6999.00, 50, 500, 0.22, 1),
('P002', '小米 14 Pro', 6, '小米', '14 Pro', '台', 3999.00, 4999.00, 50, 500, 0.21, 1),
('P003', '华为 MatePad Pro', 7, '华为', 'MatePad Pro 13.2', '台', 4499.00, 5499.00, 30, 300, 0.58, 1),
('P004', '小米平板 6 Pro', 7, '小米', '平板 6 Pro', '台', 2499.00, 2999.00, 30, 300, 0.49, 1),
('P005', '华为 Watch GT 4', 8, '华为', 'Watch GT 4', '台', 1288.00, 1588.00, 100, 1000, 0.05, 1),
('P006', '小米手环 8 Pro', 8, '小米', '手环 8 Pro', '台', 299.00, 399.00, 200, 2000, 0.03, 1),
('P007', '海尔智家空调', 9, '海尔', 'KFR-35GW', '台', 2499.00, 3299.00, 20, 200, 35.00, 1),
('P008', '美的变频空调', 9, '美的', 'KFR-35GW/N8', '台', 2299.00, 2999.00, 20, 200, 32.00, 1),
('P009', '海尔对开门冰箱', 10, '海尔', 'BCD-540W', '台', 3999.00, 4999.00, 10, 100, 85.00, 1),
('P010', '美的多门冰箱', 10, '美的', 'BCD-508W', '台', 3599.00, 4599.00, 10, 100, 80.00, 1),
('P011', '海尔滚筒洗衣机', 11, '海尔', 'EG10014', '台', 2799.00, 3599.00, 15, 150, 65.00, 1),
('P012', '美的波轮洗衣机', 11, '美的', 'MB100V31', '台', 1799.00, 2299.00, 15, 150, 55.00, 1),
('P013', 'TCL 智能电视 65 寸', 12, 'TCL', '65Q10H', '台', 3499.00, 4499.00, 10, 100, 25.00, 1),
('P014', '海信激光电视', 12, '海信', '88L5G', '台', 9999.00, 12999.00, 5, 50, 40.00, 1),
('P015', '华为超级快充', 13, '华为', '66W', '个', 99.00, 149.00, 500, 5000, 0.15, 1),
('P016', '小米快充充电器', 13, '小米', '33W', '个', 49.00, 79.00, 500, 5000, 0.12, 1),
('P017', '华为 Type-C 数据线', 14, '华为', '5A', '条', 29.00, 49.00, 1000, 10000, 0.05, 1),
('P018', '小米数据线', 14, '小米', '快充版', '条', 19.00, 29.00, 1000, 10000, 0.04, 1),
('P019', '华为手机保护壳', 15, '华为', 'Mate 60', '个', 49.00, 99.00, 500, 5000, 0.03, 1),
('P020', '小米手机保护壳', 15, '小米', '14 Pro', '个', 39.00, 69.00, 500, 5000, 0.03, 1),
('P021', '联想 ThinkPad X1', 18, '联想', 'X1 Carbon', '台', 8999.00, 11999.00, 20, 200, 1.12, 1),
('P022', '华为 MateBook X Pro', 18, '华为', 'MateBook X Pro', '台', 7999.00, 9999.00, 20, 200, 1.26, 1),
('P023', '联想天逸台式机', 19, '联想', '天逸 510S', '台', 4499.00, 5499.00, 10, 100, 8.50, 1),
('P024', '华为 MateStation', 19, '华为', 'MateStation X', '台', 6499.00, 7999.00, 10, 100, 7.80, 1),
('P025', '华为 MatePad 11', 20, '华为', 'MatePad 11', '台', 2499.00, 2999.00, 30, 300, 0.45, 1),
('P026', '小米 Pad 6', 20, '小米', 'Pad 6', '台', 1999.00, 2499.00, 30, 300, 0.49, 1),
('P027', '华为 nova 12 Pro', 16, '华为', 'nova 12 Pro', '台', 3499.00, 4299.00, 50, 500, 0.20, 1),
('P028', '小米 Redmi Note 13', 16, '小米', 'Redmi Note 13', '台', 1299.00, 1599.00, 100, 1000, 0.19, 1),
('P029', '格力空调', 9, '格力', 'KFR-35GW', '台', 2699.00, 3499.00, 20, 200, 33.00, 1),
('P030', 'TCL 冰箱', 10, 'TCL', 'BCD-456W', '台', 2999.00, 3799.00, 10, 100, 75.00, 1);

-- 2.4 插入仓库数据
INSERT INTO warehouses (warehouse_code, warehouse_name, address, city, province, manager, manager_phone, capacity, status) VALUES
('WH001', '深圳宝安仓库', '宝安区西乡大道', '深圳', '广东', '陈经理', '13900139001', 10000.00, 1),
('WH002', '广州白云仓库', '白云区石井大道', '广州', '广东', '黄经理', '13900139002', 8000.00, 1),
('WH003', '北京顺义仓库', '顺义区空港工业区', '北京', '北京', '杨经理', '13900139003', 12000.00, 1),
('WH004', '上海浦东仓库', '浦东新区祝桥路', '上海', '上海', '周经理', '13900139004', 15000.00, 1),
('WH005', '武汉江夏仓库', '江夏区藏龙岛', '武汉', '湖北', '吴经理', '13900139005', 6000.00, 1);

-- 2.5 插入客户数据
INSERT INTO customers (customer_code, customer_name, customer_type, contact_person, contact_phone, contact_email, address, city, province, credit_limit, credit_level, status) VALUES
('CUS001', '京东世纪贸易有限公司', 'enterprise', '马云', '13700137001', 'mayun@jd.com', '大兴区亦庄', '北京', '北京', 1000000.00, 'A', 1),
('CUS002', '天猫网络技术有限公司', 'enterprise', '马化腾', '13700137002', 'matengten@tmall.com', '余杭区文一西路', '杭州', '浙江', 1000000.00, 'A', 1),
('CUS003', '苏宁易购集团股份有限公司', 'enterprise', '张近东', '13700137003', 'zhangjindong@suning.com', '玄武区苏宁大道', '南京', '江苏', 800000.00, 'A', 1),
('CUS004', '国美控股集团有限公司', 'enterprise', '黄光裕', '13700137004', 'huangguangyu@gome.com', '大兴区黄村', '北京', '北京', 500000.00, 'B', 1),
('CUS005', '唯品会信息科技有限公司', 'enterprise', '沈亚', '13700137005', 'shenya@vip.com', '荔湾区芳村', '广州', '广东', 500000.00, 'B', 1),
('CUS006', '拼多多商贸有限公司', 'enterprise', '黄峥', '13700137006', 'huangzheng@pdd.com', '长宁区金钟路', '上海', '上海', 800000.00, 'A', 1),
('CUS007', '抖音电子商务有限公司', 'enterprise', '张一鸣', '13700137007', 'zhangyiming@douyin.com', '海淀区北三环', '北京', '北京', 600000.00, 'A', 1),
('CUS008', '快手电子商务有限公司', 'enterprise', '宿华', '13700137008', 'suhua@kuaishou.com', '海淀区上地', '北京', '北京', 400000.00, 'B', 1),
('CUS009', '张三', 'retail', '张三', '13600136001', 'zhangsan@email.com', '南山区科技园', '深圳', '广东', 10000.00, 'C', 1),
('CUS010', '李四', 'retail', '李四', '13600136002', 'lisi@email.com', '天河区珠江新城', '广州', '广东', 10000.00, 'C', 1),
('CUS011', '王五', 'retail', '王五', '13600136003', 'wangwu@email.com', '浦东新区陆家嘴', '上海', '上海', 10000.00, 'C', 1),
('CUS012', '赵六', 'retail', '赵六', '13600136004', 'zhaoliu@email.com', '武昌区中南路', '武汉', '湖北', 10000.00, 'C', 1);

-- 2.6 插入初始库存数据
INSERT INTO inventory (warehouse_id, product_id, quantity, locked_quantity, last_stock_check) VALUES
(1, 1, 200, 10, NOW()),
(1, 2, 150, 5, NOW()),
(1, 3, 80, 2, NOW()),
(1, 5, 300, 20, NOW()),
(1, 6, 500, 30, NOW()),
(1, 15, 2000, 100, NOW()),
(1, 16, 1500, 80, NOW()),
(1, 17, 5000, 200, NOW()),
(1, 18, 4000, 150, NOW()),
(2, 1, 100, 5, NOW()),
(2, 2, 120, 8, NOW()),
(2, 7, 50, 3, NOW()),
(2, 8, 60, 4, NOW()),
(2, 9, 30, 2, NOW()),
(2, 10, 35, 2, NOW()),
(3, 1, 150, 10, NOW()),
(3, 2, 100, 5, NOW()),
(3, 21, 40, 2, NOW()),
(3, 22, 35, 2, NOW()),
(3, 23, 25, 1, NOW()),
(3, 24, 20, 1, NOW()),
(4, 1, 180, 12, NOW()),
(4, 2, 130, 7, NOW()),
(4, 13, 40, 2, NOW()),
(4, 14, 15, 1, NOW()),
(4, 29, 45, 3, NOW()),
(5, 1, 80, 4, NOW()),
(5, 2, 90, 5, NOW()),
(5, 3, 50, 2, NOW()),
(5, 4, 60, 3, NOW()),
(5, 25, 70, 4, NOW()),
(5, 26, 80, 5, NOW());

-- ============================================================
-- 3. 生成历史订单数据（存储过程）
-- ============================================================

DELIMITER $$

-- 创建生成采购订单的存储过程
CREATE PROCEDURE generate_purchase_orders(IN num_orders INT)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE v_order_no VARCHAR(30);
    DECLARE v_supplier_id INT;
    DECLARE v_warehouse_id INT;
    DECLARE v_order_date DATE;
    DECLARE v_expected_date DATE;
    DECLARE v_total_amount DECIMAL(12,2);
    DECLARE v_status VARCHAR(20);
    DECLARE v_item_count INT;
    DECLARE v_j INT;
    DECLARE v_product_id INT;
    DECLARE v_quantity INT;
    DECLARE v_unit_price DECIMAL(10,2);
    DECLARE v_subtotal DECIMAL(12,2);

    WHILE i < num_orders DO
        SET v_order_no = CONCAT('PO', DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL FLOOR(RAND()*90) DAY), '%Y%m%d'), LPAD(i+1, 4, '0'));
        SET v_supplier_id = FLOOR(1 + RAND()*10);
        SET v_warehouse_id = FLOOR(1 + RAND()*5);
        SET v_order_date = DATE_SUB(CURDATE(), INTERVAL FLOOR(RAND()*90) DAY);
        SET v_expected_date = DATE_ADD(v_order_date, INTERVAL 7 DAY);
        SET v_total_amount = 0;
        SET v_status = CASE FLOOR(RAND()*4) WHEN 0 THEN 'completed' WHEN 1 THEN 'shipped' WHEN 2 THEN 'processing' ELSE 'pending' END;

        INSERT INTO purchase_orders (order_no, supplier_id, warehouse_id, order_date, expected_date, total_amount, status, created_at)
        VALUES (v_order_no, v_supplier_id, v_warehouse_id, v_order_date, v_expected_date, 0, v_status, NOW());

        SET v_item_count = FLOOR(1 + RAND()*5);
        SET v_j = 0;

        WHILE v_j < v_item_count DO
            SET v_product_id = FLOOR(1 + RAND()*30);
            SET v_quantity = FLOOR(10 + RAND()*100);
            SELECT cost_price INTO v_unit_price FROM products WHERE product_id = v_product_id;
            SET v_subtotal = v_unit_price * v_quantity;
            SET v_total_amount = v_total_amount + v_subtotal;

            INSERT INTO purchase_order_items (order_id, product_id, quantity, unit_price, subtotal, status)
            VALUES (LAST_INSERT_ID(), v_product_id, v_quantity, v_unit_price, v_subtotal, v_status);

            SET v_j = v_j + 1;
        END WHILE;

        UPDATE purchase_orders SET total_amount = v_total_amount, final_amount = v_total_amount * 1.13 WHERE order_no = v_order_no;

        SET i = i + 1;
    END WHILE;
END$$

-- 创建生成销售订单的存储过程
CREATE PROCEDURE generate_sales_orders(IN num_orders INT)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE v_order_no VARCHAR(30);
    DECLARE v_customer_id INT;
    DECLARE v_warehouse_id INT;
    DECLARE v_order_date DATE;
    DECLARE v_total_amount DECIMAL(12,2);
    DECLARE v_status VARCHAR(20);
    DECLARE v_payment_status VARCHAR(20);
    DECLARE v_item_count INT;
    DECLARE v_j INT;
    DECLARE v_product_id INT;
    DECLARE v_quantity INT;
    DECLARE v_unit_price DECIMAL(10,2);
    DECLARE v_cost_price DECIMAL(10,2);
    DECLARE v_subtotal DECIMAL(12,2);

    WHILE i < num_orders DO
        SET v_order_no = CONCAT('SO', DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL FLOOR(RAND()*90) DAY), '%Y%m%d'), LPAD(i+1, 4, '0'));
        SET v_customer_id = FLOOR(1 + RAND()*12);
        SET v_warehouse_id = FLOOR(1 + RAND()*5);
        SET v_order_date = DATE_SUB(CURDATE(), INTERVAL FLOOR(RAND()*90) DAY);
        SET v_total_amount = 0;
        SET v_status = CASE FLOOR(RAND()*4) WHEN 0 THEN 'completed' WHEN 1 THEN 'shipped' WHEN 2 THEN 'processing' ELSE 'pending' END;
        SET v_payment_status = CASE FLOOR(RAND()*3) WHEN 0 THEN 'paid' WHEN 1 THEN 'partial' ELSE 'unpaid' END;

        INSERT INTO sales_orders (order_no, customer_id, warehouse_id, order_date, total_amount, status, payment_status, created_at)
        VALUES (v_order_no, v_customer_id, v_warehouse_id, v_order_date, 0, v_status, v_payment_status, NOW());

        SET v_item_count = FLOOR(1 + RAND()*5);
        SET v_j = 0;

        WHILE v_j < v_item_count DO
            SET v_product_id = FLOOR(1 + RAND()*30);
            SET v_quantity = FLOOR(1 + RAND()*10);
            SELECT selling_price, cost_price INTO v_unit_price, v_cost_price FROM products WHERE product_id = v_product_id;
            SET v_subtotal = v_unit_price * v_quantity;
            SET v_total_amount = v_total_amount + v_subtotal;

            INSERT INTO sales_order_items (order_id, product_id, quantity, unit_price, cost_price, subtotal, status)
            VALUES (LAST_INSERT_ID(), v_product_id, v_quantity, v_unit_price, v_cost_price, v_subtotal, v_status);

            SET v_j = v_j + 1;
        END WHILE;

        UPDATE sales_orders SET total_amount = v_total_amount, final_amount = v_total_amount * 1.13 WHERE order_no = v_order_no;

        SET i = i + 1;
    END WHILE;
END$$

DELIMITER ;

-- 执行存储过程生成模拟数据
CALL generate_purchase_orders(200);
CALL generate_sales_orders(300);

-- 删除存储过程
DROP PROCEDURE IF EXISTS generate_purchase_orders;
DROP PROCEDURE IF EXISTS generate_sales_orders;

-- ============================================================
-- 4. ODS 层表 - 操作数据存储层（原始数据镜像）
-- ============================================================

USE erp_ods;

-- ODS 层采用与源库相同的表结构，增加 ETL 时间戳
CREATE TABLE IF NOT EXISTS ods_suppliers AS SELECT *, NOW() as etl_time FROM erp_source.suppliers WHERE 1=0;
ALTER TABLE ods_suppliers ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_categories AS SELECT *, NOW() as etl_time FROM erp_source.categories WHERE 1=0;
ALTER TABLE ods_categories ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_products AS SELECT *, NOW() as etl_time FROM erp_source.products WHERE 1=0;
ALTER TABLE ods_products ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_warehouses AS SELECT *, NOW() as etl_time FROM erp_source.warehouses WHERE 1=0;
ALTER TABLE ods_warehouses ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_inventory AS SELECT *, NOW() as etl_time FROM erp_source.inventory WHERE 1=0;
ALTER TABLE ods_inventory ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_customers AS SELECT *, NOW() as etl_time FROM erp_source.customers WHERE 1=0;
ALTER TABLE ods_customers ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_purchase_orders AS SELECT *, NOW() as etl_time FROM erp_source.purchase_orders WHERE 1=0;
ALTER TABLE ods_purchase_orders ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_purchase_order_items AS SELECT *, NOW() as etl_time FROM erp_source.purchase_order_items WHERE 1=0;
ALTER TABLE ods_purchase_order_items ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_sales_orders AS SELECT *, NOW() as etl_time FROM erp_source.sales_orders WHERE 1=0;
ALTER TABLE ods_sales_orders ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_sales_order_items AS SELECT *, NOW() as etl_time FROM erp_source.sales_order_items WHERE 1=0;
ALTER TABLE ods_sales_order_items ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_purchase_inbound AS SELECT *, NOW() as etl_time FROM erp_source.purchase_inbound WHERE 1=0;
ALTER TABLE ods_purchase_inbound ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_purchase_inbound_items AS SELECT *, NOW() as etl_time FROM erp_source.purchase_inbound_items WHERE 1=0;
ALTER TABLE ods_purchase_inbound_items ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_sales_outbound AS SELECT *, NOW() as etl_time FROM erp_source.sales_outbound WHERE 1=0;
ALTER TABLE ods_sales_outbound ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_sales_outbound_items AS SELECT *, NOW() as etl_time FROM erp_source.sales_outbound_items WHERE 1=0;
ALTER TABLE ods_sales_outbound_items ADD INDEX idx_etl_time (etl_time);

CREATE TABLE IF NOT EXISTS ods_inventory_transaction AS SELECT *, NOW() as etl_time FROM erp_source.inventory_transaction WHERE 1=0;
ALTER TABLE ods_inventory_transaction ADD INDEX idx_etl_time (etl_time);

-- ============================================================
-- 5. DWD 层表 - 明细数据层（清洗后的明细数据）
-- ============================================================

USE erp_dwd;

-- 5.1 采购订单事实表
CREATE TABLE IF NOT EXISTS dwd_purchase_order_fact (
    order_sk BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(30) NOT NULL,
    order_date DATE,
    supplier_id INT,
    supplier_code VARCHAR(20),
    supplier_name VARCHAR(100),
    warehouse_id INT,
    warehouse_code VARCHAR(20),
    warehouse_name VARCHAR(100),
    product_id INT,
    product_code VARCHAR(30),
    product_name VARCHAR(200),
    category_id INT,
    category_name VARCHAR(100),
    quantity INT,
    unit_price DECIMAL(10,2),
    subtotal DECIMAL(12,2),
    tax_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    order_status VARCHAR(20),
    data_source VARCHAR(20) DEFAULT 'erp',
    created_at DATETIME,
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order_date (order_date),
    INDEX idx_supplier_id (supplier_id),
    INDEX idx_product_id (product_id),
    INDEX idx_warehouse_id (warehouse_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购订单事实表';

-- 5.2 销售订单事实表
CREATE TABLE IF NOT EXISTS dwd_sales_order_fact (
    order_sk BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(30) NOT NULL,
    order_date DATE,
    customer_id INT,
    customer_code VARCHAR(20),
    customer_name VARCHAR(100),
    customer_type VARCHAR(20),
    warehouse_id INT,
    warehouse_code VARCHAR(20),
    warehouse_name VARCHAR(100),
    product_id INT,
    product_code VARCHAR(30),
    product_name VARCHAR(200),
    category_id INT,
    category_name VARCHAR(100),
    quantity INT,
    unit_price DECIMAL(10,2),
    cost_price DECIMAL(10,2),
    profit DECIMAL(12,2),
    subtotal DECIMAL(12,2),
    tax_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    order_status VARCHAR(20),
    payment_status VARCHAR(20),
    data_source VARCHAR(20) DEFAULT 'erp',
    created_at DATETIME,
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order_date (order_date),
    INDEX idx_customer_id (customer_id),
    INDEX idx_product_id (product_id),
    INDEX idx_warehouse_id (warehouse_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售订单事实表';

-- 5.3 库存事实表
CREATE TABLE IF NOT EXISTS dwd_inventory_fact (
    inventory_sk BIGINT PRIMARY KEY AUTO_INCREMENT,
    warehouse_id INT,
    warehouse_code VARCHAR(20),
    warehouse_name VARCHAR(100),
    product_id INT,
    product_code VARCHAR(30),
    product_name VARCHAR(200),
    category_id INT,
    category_name VARCHAR(100),
    quantity INT,
    locked_quantity INT,
    available_quantity INT,
    stock_date DATE,
    data_source VARCHAR(20) DEFAULT 'erp',
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock_date (stock_date),
    INDEX idx_product_id (product_id),
    INDEX idx_warehouse_id (warehouse_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存事实表';

-- 5.4 入库事实表
CREATE TABLE IF NOT EXISTS dwd_inbound_fact (
    inbound_sk BIGINT PRIMARY KEY AUTO_INCREMENT,
    inbound_no VARCHAR(30) NOT NULL,
    inbound_date DATE,
    order_id INT,
    order_no VARCHAR(30),
    warehouse_id INT,
    warehouse_code VARCHAR(20),
    warehouse_name VARCHAR(100),
    supplier_id INT,
    supplier_code VARCHAR(20),
    supplier_name VARCHAR(100),
    product_id INT,
    product_code VARCHAR(30),
    product_name VARCHAR(200),
    quantity INT,
    unit_price DECIMAL(10,2),
    subtotal DECIMAL(12,2),
    batch_no VARCHAR(50),
    data_source VARCHAR(20) DEFAULT 'erp',
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_inbound_date (inbound_date),
    INDEX idx_product_id (product_id),
    INDEX idx_warehouse_id (warehouse_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='入库事实表';

-- 5.5 出库事实表
CREATE TABLE IF NOT EXISTS dwd_outbound_fact (
    outbound_sk BIGINT PRIMARY KEY AUTO_INCREMENT,
    outbound_no VARCHAR(30) NOT NULL,
    outbound_date DATE,
    order_id INT,
    order_no VARCHAR(30),
    warehouse_id INT,
    warehouse_code VARCHAR(20),
    warehouse_name VARCHAR(100),
    customer_id INT,
    customer_code VARCHAR(20),
    customer_name VARCHAR(100),
    product_id INT,
    product_code VARCHAR(30),
    product_name VARCHAR(200),
    quantity INT,
    unit_price DECIMAL(10,2),
    subtotal DECIMAL(12,2),
    shipping_method VARCHAR(50),
    shipping_no VARCHAR(100),
    data_source VARCHAR(20) DEFAULT 'erp',
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_outbound_date (outbound_date),
    INDEX idx_product_id (product_id),
    INDEX idx_warehouse_id (warehouse_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出库事实表';

-- ============================================================
-- 6. DWS 层表 - 汇总数据层（轻度汇总）
-- ============================================================

USE erp_dws;

-- 6.1 供应商日汇总
CREATE TABLE IF NOT EXISTS dws_supplier_daily (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    supplier_id INT,
    supplier_code VARCHAR(20),
    supplier_name VARCHAR(100),
    stat_date DATE,
    order_count INT DEFAULT 0,
    total_quantity INT DEFAULT 0,
    total_amount DECIMAL(12,2) DEFAULT 0.00,
    completed_count INT DEFAULT 0,
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_supplier_date (supplier_id, stat_date),
    INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='供应商日汇总表';

-- 6.2 客户日汇总
CREATE TABLE IF NOT EXISTS dws_customer_daily (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    customer_code VARCHAR(20),
    customer_name VARCHAR(100),
    customer_type VARCHAR(20),
    stat_date DATE,
    order_count INT DEFAULT 0,
    total_quantity INT DEFAULT 0,
    total_amount DECIMAL(12,2) DEFAULT 0.00,
    paid_amount DECIMAL(12,2) DEFAULT 0.00,
    completed_count INT DEFAULT 0,
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_customer_date (customer_id, stat_date),
    INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户日汇总表';

-- 6.3 商品日汇总
CREATE TABLE IF NOT EXISTS dws_product_daily (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id INT,
    product_code VARCHAR(30),
    product_name VARCHAR(200),
    category_id INT,
    category_name VARCHAR(100),
    stat_date DATE,
    sales_quantity INT DEFAULT 0,
    sales_amount DECIMAL(12,2) DEFAULT 0.00,
    sales_profit DECIMAL(12,2) DEFAULT 0.00,
    purchase_quantity INT DEFAULT 0,
    purchase_amount DECIMAL(12,2) DEFAULT 0.00,
    inbound_quantity INT DEFAULT 0,
    outbound_quantity INT DEFAULT 0,
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_product_date (product_id, stat_date),
    INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品日汇总表';

-- 6.4 仓库日汇总
CREATE TABLE IF NOT EXISTS dws_warehouse_daily (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    warehouse_id INT,
    warehouse_code VARCHAR(20),
    warehouse_name VARCHAR(100),
    stat_date DATE,
    inbound_count INT DEFAULT 0,
    inbound_quantity INT DEFAULT 0,
    outbound_count INT DEFAULT 0,
    outbound_quantity INT DEFAULT 0,
    inventory_quantity INT DEFAULT 0,
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_warehouse_date (warehouse_id, stat_date),
    INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='仓库日汇总表';

-- 6.5 品类日汇总
CREATE TABLE IF NOT EXISTS dws_category_daily (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    category_id INT,
    category_name VARCHAR(100),
    stat_date DATE,
    sales_quantity INT DEFAULT 0,
    sales_amount DECIMAL(12,2) DEFAULT 0.00,
    sales_profit DECIMAL(12,2) DEFAULT 0.00,
    purchase_quantity INT DEFAULT 0,
    purchase_amount DECIMAL(12,2) DEFAULT 0.00,
    product_count INT DEFAULT 0,
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_category_date (category_id, stat_date),
    INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品类日汇总表';

-- ============================================================
-- 7. ADS 层表 - 应用数据层（面向应用的汇总）
-- ============================================================

USE erp_ads;

-- 7.1 销售驾驶舱指标
CREATE TABLE IF NOT EXISTS ads_sales_dashboard (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stat_date DATE,
    total_sales_amount DECIMAL(12,2) DEFAULT 0.00,
    total_sales_quantity INT DEFAULT 0,
    total_profit DECIMAL(12,2) DEFAULT 0.00,
    order_count INT DEFAULT 0,
    customer_count INT DEFAULT 0,
    product_count INT DEFAULT 0,
    mom_sales_growth DECIMAL(8,4) DEFAULT 0.0000,
    yoy_sales_growth DECIMAL(8,4) DEFAULT 0.0000,
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售驾驶舱指标表';

-- 7.2 销售排名 TOP10
CREATE TABLE IF NOT EXISTS ads_sales_ranking (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stat_date DATE,
    ranking_type VARCHAR(20),
    item_id INT,
    item_name VARCHAR(200),
    ranking_value DECIMAL(12,2),
    ranking INT,
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stat_date (stat_date),
    INDEX idx_ranking_type (ranking_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售排名表';

-- 7.3 库存预警
CREATE TABLE IF NOT EXISTS ads_inventory_warning (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    warehouse_id INT,
    warehouse_name VARCHAR(100),
    product_id INT,
    product_name VARCHAR(200),
    current_quantity INT,
    min_stock INT,
    max_stock INT,
    warning_type VARCHAR(20),
    warning_level VARCHAR(10),
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_warning_type (warning_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存预警表';

-- 7.4 供应商分析
CREATE TABLE IF NOT EXISTS ads_supplier_analysis (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stat_date DATE,
    supplier_id INT,
    supplier_name VARCHAR(100),
    total_orders INT,
    total_amount DECIMAL(12,2),
    avg_delivery_days INT,
    on_time_rate DECIMAL(5,4),
    return_rate DECIMAL(5,4),
    credit_score INT,
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_supplier_stat (supplier_id, stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='供应商分析表';

-- 7.5 客户分析
CREATE TABLE IF NOT EXISTS ads_customer_analysis (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stat_date DATE,
    customer_id INT,
    customer_name VARCHAR(100),
    customer_type VARCHAR(20),
    total_orders INT,
    total_amount DECIMAL(12,2),
    avg_order_value DECIMAL(12,2),
    purchase_frequency INT,
    last_order_date DATE,
    customer_value VARCHAR(10),
    etl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_customer_stat (customer_id, stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户分析表';

-- ============================================================
-- 8. ETL 日志表
-- ============================================================

USE erp_ods;

CREATE TABLE IF NOT EXISTS etl_log (
    log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_name VARCHAR(100),
    table_name VARCHAR(100),
    start_time DATETIME,
    end_time DATETIME,
    status VARCHAR(20),
    records_inserted INT DEFAULT 0,
    records_updated INT DEFAULT 0,
    records_failed INT DEFAULT 0,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_name (task_name),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ETL 日志表';

CREATE TABLE IF NOT EXISTS etl_job_status (
    job_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    job_name VARCHAR(100) NOT NULL UNIQUE,
    last_run_time DATETIME,
    last_status VARCHAR(20),
    next_run_time DATETIME,
    enabled TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_job_name (job_name),
    INDEX idx_status (last_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ETL 任务状态表';

-- 初始化 ETL 任务状态
INSERT INTO etl_job_status (job_name, last_status, enabled) VALUES
('ods_full_sync', 'pending', 1),
('ods_incremental_sync', 'pending', 1),
('dwd_purchase_sync', 'pending', 1),
('dwd_sales_sync', 'pending', 1),
('dwd_inventory_sync', 'pending', 1),
('dws_daily_agg', 'pending', 1),
('ads_dashboard', 'pending', 1);

-- ============================================================
-- 初始化完成
-- ============================================================

SELECT 'AI数据融合 数据库初始化完成!' AS message;
SELECT '源库 (erp_source):', COUNT(*) AS tables FROM information_schema.tables WHERE table_schema = 'erp_source';
SELECT 'ODS 库 (erp_ods):', COUNT(*) AS tables FROM information_schema.tables WHERE table_schema = 'erp_ods';
SELECT 'DWD 库 (erp_dwd):', COUNT(*) AS tables FROM information_schema.tables WHERE table_schema = 'erp_dwd';
SELECT 'DWS 库 (erp_dws):', COUNT(*) AS tables FROM information_schema.tables WHERE table_schema = 'erp_dws';
SELECT 'ADS 库 (erp_ads):', COUNT(*) AS tables FROM information_schema.tables WHERE table_schema = 'erp_ads';
