-- Metabase 配置 SQL 脚本
-- 用于创建 BI 报表所需的视图和预聚合表
-- 数据库：erp_source（源库，包含业务数据）

USE erp_source;

-- ============================================
-- 1. 创建 BI 视图层（方便 Metabase 使用）
-- ============================================

-- 销售汇总视图 - 月度销售趋势
CREATE OR REPLACE VIEW v_sales_summary AS
SELECT
    DATE_FORMAT(o.order_date, '%Y-%m') AS stat_month,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.final_amount) AS total_amount,
    AVG(o.final_amount) AS avg_order_value,
    SUM(oi.quantity) AS total_quantity
FROM sales_orders o
JOIN sales_order_items oi ON o.order_id = oi.order_id
GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
ORDER BY stat_month;

-- 产品销售视图
CREATE OR REPLACE VIEW v_product_sales AS
SELECT
    p.product_id,
    p.product_name,
    c.category_name AS category,
    COUNT(DISTINCT oi.order_id) AS order_count,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.subtotal) AS total_amount
FROM products p
JOIN sales_order_items oi ON p.product_id = oi.product_id
JOIN sales_orders o ON oi.order_id = o.order_id
LEFT JOIN categories c ON p.category_id = c.category_id
GROUP BY p.product_id, p.product_name, c.category_name;

-- 客户分析视图
CREATE OR REPLACE VIEW v_customer_analysis AS
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_type,
    c.city,
    c.province,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.final_amount) AS total_amount,
    AVG(o.final_amount) AS avg_order_value,
    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS last_order_date
FROM customers c
LEFT JOIN sales_orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name, c.customer_type, c.city, c.province;

-- 品类分析视图
CREATE OR REPLACE VIEW v_category_analysis AS
SELECT
    c.category_name AS category,
    COUNT(DISTINCT p.product_id) AS product_count,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.subtotal) AS total_amount,
    ROUND(SUM(oi.subtotal) * 100.0 / (SELECT SUM(subtotal) FROM sales_order_items), 2) AS sales_ratio
FROM products p
JOIN sales_order_items oi ON p.product_id = oi.product_id
LEFT JOIN categories c ON p.category_id = c.category_id
GROUP BY c.category_name;

-- 每日销售视图
CREATE OR REPLACE VIEW v_daily_sales AS
SELECT
    DATE(o.order_date) AS stat_date,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.final_amount) AS total_amount,
    AVG(o.final_amount) AS avg_order_value
FROM sales_orders o
GROUP BY DATE(o.order_date)
ORDER BY stat_date DESC;

-- ============================================
-- 2. 创建 KPI 汇总表（用于仪表板卡片）
-- ============================================

CREATE OR REPLACE VIEW v_kpi_summary AS
SELECT
    '总销售额' AS kpi_name,
    CONCAT('¥', FORMAT(SUM(final_amount), 2)) AS kpi_value,
    'amount' AS kpi_type,
    SUM(final_amount) AS raw_value
FROM sales_orders
UNION ALL
SELECT
    '总订单数',
    CAST(COUNT(*) AS CHAR),
    'count',
    CAST(COUNT(*) AS DECIMAL(12,2))
FROM sales_orders
UNION ALL
SELECT
    '总销售量',
    CAST(SUM(oi.quantity) AS CHAR),
    'quantity',
    CAST(SUM(oi.quantity) AS DECIMAL(12,2))
FROM sales_order_items oi
UNION ALL
SELECT
    '客户总数',
    CAST(COUNT(DISTINCT customer_id) AS CHAR),
    'count',
    CAST(COUNT(DISTINCT customer_id) AS DECIMAL(12,2))
FROM sales_orders
UNION ALL
SELECT
    '产品种类数',
    CAST(COUNT(DISTINCT product_id) AS CHAR),
    'count',
    CAST(COUNT(DISTINCT product_id) AS DECIMAL(12,2))
FROM sales_order_items;

-- ============================================
-- 3. 创建 Top 排行视图
-- ============================================

-- 产品销量 Top10
CREATE OR REPLACE VIEW v_product_top10 AS
SELECT
    p.product_name,
    c.category_name AS category,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.subtotal) AS total_amount
FROM products p
JOIN sales_order_items oi ON p.product_id = oi.product_id
LEFT JOIN categories c ON p.category_id = c.category_id
GROUP BY p.product_name, c.category_name
ORDER BY total_quantity DESC
LIMIT 10;

-- 客户消费 Top10
CREATE OR REPLACE VIEW v_customer_top10 AS
SELECT
    c.customer_name,
    c.customer_type,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.final_amount) AS total_amount
FROM customers c
JOIN sales_orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_name, c.customer_type
ORDER BY total_amount DESC
LIMIT 10;

-- ============================================
-- 4. 创建日期维度表（用于时间序列分析）
-- ============================================

CREATE TABLE IF NOT EXISTS dim_date (
    date_id DATE PRIMARY KEY,
    year INT,
    month INT,
    day INT,
    quarter INT,
    month_name VARCHAR(20),
    day_of_week VARCHAR(20),
    is_weekend BOOLEAN
);

-- 插入 2024-2027 年的日期维度数据
INSERT INTO dim_date (date_id, year, month, day, quarter, month_name, day_of_week, is_weekend)
SELECT
    d AS date_id,
    YEAR(d) AS year,
    MONTH(d) AS month,
    DAY(d) AS day,
    QUARTER(d) AS quarter,
    MONTHNAME(d) AS month_name,
    DAYNAME(d) AS day_of_week,
    CASE WHEN WEEKDAY(d) >= 5 THEN TRUE ELSE FALSE END AS is_weekend
FROM (
    SELECT DATE_ADD('2024-01-01', INTERVAL seq DAY) AS d
    FROM (
        SELECT a.N + b.N * 10 + c.N * 100 AS seq
        FROM
            (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
            (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
            (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c
    ) nums
    WHERE DATE_ADD('2024-01-01', INTERVAL seq DAY) <= '2027-12-31'
) dates
ON DUPLICATE KEY UPDATE year = VALUES(year);

-- ============================================
-- 5. 授权 Metabase 用户访问
-- ============================================

-- 创建 Metabase 专用用户
CREATE USER IF NOT EXISTS 'metabase'@'%' IDENTIFIED BY 'metabase123';
GRANT SELECT ON erp_source.* TO 'metabase'@'%';
FLUSH PRIVILEGES;

-- ============================================
-- 6. 验证视图
-- ============================================

-- 测试查询
SELECT * FROM v_kpi_summary;
SELECT * FROM v_sales_summary LIMIT 5;
SELECT * FROM v_product_top10;
SELECT * FROM v_customer_top10;

SELECT '视图创建完成！' AS status;
