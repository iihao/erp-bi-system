-- AI数据融合平台 ETL 功能增强迁移脚本
-- 创建时间：2026-03-16
-- 功能：数据中台 ETL 完整功能支持

-- ============================================
-- 1. 数据源管理表
-- ============================================

CREATE TABLE IF NOT EXISTS etl_datasources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COMMENT '数据源名称',
    type TEXT NOT NULL COMMENT '数据源类型：mysql/postgresql/csv/excel/api',
    host TEXT COMMENT '主机地址',
    port INTEGER COMMENT '端口',
    database TEXT COMMENT '数据库名',
    username TEXT COMMENT '用户名',
    password TEXT COMMENT '密码（加密存储）',
    connection_string TEXT COMMENT '连接字符串',
    file_path TEXT COMMENT '文件路径（CSV/Excel）',
    api_url TEXT COMMENT 'API 地址',
    description TEXT COMMENT '描述',
    config_json TEXT COMMENT '扩展配置（JSON）',
    is_enabled INTEGER DEFAULT 1 COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_datasource_type ON etl_datasources(type);
CREATE INDEX IF NOT EXISTS idx_datasource_enabled ON etl_datasources(is_enabled);

-- ============================================
-- 2. ETL 转换任务表
-- ============================================

CREATE TABLE IF NOT EXISTS etl_transform_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COMMENT '任务名称',
    source_datasource_id INTEGER COMMENT '源数据源 ID',
    source_table TEXT NOT NULL COMMENT '源表名',
    target_datasource_id INTEGER COMMENT '目标数据源 ID',
    target_table TEXT NOT NULL COMMENT '目标表名',
    transform_rules_json TEXT COMMENT '转换规则（JSON）',
    extract_mode TEXT DEFAULT 'full' COMMENT '抽取模式：full/incremental',
    extract_field TEXT COMMENT '增量字段',
    batch_size INTEGER DEFAULT 1000 COMMENT '批量大小',
    description TEXT COMMENT '描述',
    is_enabled INTEGER DEFAULT 1 COMMENT '是否启用',
    last_run_at TIMESTAMP COMMENT '最后执行时间',
    last_status TEXT COMMENT '最后状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_datasource_id) REFERENCES etl_datasources(id),
    FOREIGN KEY (target_datasource_id) REFERENCES etl_datasources(id)
);

CREATE INDEX IF NOT EXISTS idx_transform_task_enabled ON etl_transform_tasks(is_enabled);
CREATE INDEX IF NOT EXISTS idx_transform_task_last_status ON etl_transform_tasks(last_status);

-- ============================================
-- 3. ETL 任务依赖关系表
-- ============================================

CREATE TABLE IF NOT EXISTS etl_task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL COMMENT '任务 ID',
    depends_on_task_id INTEGER NOT NULL COMMENT '依赖的任务 ID',
    dependency_type TEXT DEFAULT 'finish' COMMENT '依赖类型：finish/success/data_ready',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES etl_transform_tasks(id),
    FOREIGN KEY (depends_on_task_id) REFERENCES etl_transform_tasks(id),
    UNIQUE(task_id, depends_on_task_id)
);

CREATE INDEX IF NOT EXISTS idx_task_dep_task ON etl_task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_dep_depends ON etl_task_dependencies(depends_on_task_id);

-- ============================================
-- 4. 数据质量规则表
-- ============================================

CREATE TABLE IF NOT EXISTS etl_quality_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER COMMENT '关联任务 ID',
    table_name TEXT NOT NULL COMMENT '表名',
    field_name TEXT NOT NULL COMMENT '字段名',
    rule_type TEXT NOT NULL COMMENT '规则类型：not_null/unique/range/regex/custom',
    rule_expression TEXT COMMENT '规则表达式',
    error_message TEXT COMMENT '错误提示',
    severity TEXT DEFAULT 'warning' COMMENT '严重程度：info/warning/error/blocking',
    is_enabled INTEGER DEFAULT 1 COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES etl_transform_tasks(id)
);

CREATE INDEX IF NOT EXISTS idx_quality_rule_task ON etl_quality_rules(task_id);
CREATE INDEX IF NOT EXISTS idx_quality_rule_table ON etl_quality_rules(table_name);

-- ============================================
-- 5. 数据质量检查结果表
-- ============================================

CREATE TABLE IF NOT EXISTS etl_quality_check_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL COMMENT '规则 ID',
    task_log_id INTEGER COMMENT '任务日志 ID',
    check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '检查时间',
    total_rows INTEGER DEFAULT 0 COMMENT '总行数',
    failed_rows INTEGER DEFAULT 0 COMMENT '失败行数',
    failed_sample TEXT COMMENT '失败样本（JSON）',
    error_message TEXT COMMENT '错误信息',
    FOREIGN KEY (rule_id) REFERENCES etl_quality_rules(id),
    FOREIGN KEY (task_log_id) REFERENCES etl_task_logs(log_id)
);

CREATE INDEX IF NOT EXISTS idx_quality_result_rule ON etl_quality_check_results(rule_id);
CREATE INDEX IF NOT EXISTS idx_quality_result_log ON etl_quality_check_results(task_log_id);
CREATE INDEX IF NOT EXISTS idx_quality_result_time ON etl_quality_check_results(check_time);

-- ============================================
-- 6. 增强 ETL 任务日志表
-- ============================================

ALTER TABLE etl_task_logs ADD COLUMN task_type TEXT DEFAULT 'ETL' COMMENT '任务类型：ETL/TRANSFORM/LOAD';
ALTER TABLE etl_task_logs ADD COLUMN task_id INTEGER COMMENT '关联任务 ID';
ALTER TABLE etl_task_logs ADD COLUMN datasource_id INTEGER COMMENT '数据源 ID';
ALTER TABLE etl_task_logs ADD COLUMN source_rows INTEGER DEFAULT 0 COMMENT '源数据行数';
ALTER TABLE etl_task_logs ADD COLUMN target_rows INTEGER DEFAULT 0 COMMENT '目标数据行数';
ALTER TABLE etl_task_logs ADD COLUMN transformed_rows INTEGER DEFAULT 0 COMMENT '转换后行数';
ALTER TABLE etl_task_logs ADD COLUMN failed_rows INTEGER DEFAULT 0 COMMENT '失败行数';
ALTER TABLE etl_task_logs ADD COLUMN metrics_json TEXT COMMENT '性能指标（JSON）';

CREATE INDEX IF NOT EXISTS idx_etl_log_task_type ON etl_task_logs(task_type);
CREATE INDEX IF NOT EXISTS idx_etl_log_task_id ON etl_task_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_etl_log_time ON etl_task_logs(start_time);

-- ============================================
-- 7. 增强 ETL 调度表
-- ============================================

ALTER TABLE etl_schedules ADD COLUMN task_id INTEGER COMMENT '关联任务 ID';
ALTER TABLE etl_schedules ADD COLUMN task_type TEXT DEFAULT 'ETL' COMMENT '任务类型';
ALTER TABLE etl_schedules ADD COLUMN timezone TEXT DEFAULT 'Asia/Shanghai' COMMENT '时区';
ALTER TABLE etl_schedules ADD COLUMN retry_times INTEGER DEFAULT 0 COMMENT '重试次数';
ALTER TABLE etl_schedules ADD COLUMN retry_interval INTEGER DEFAULT 300 COMMENT '重试间隔（秒）';
ALTER TABLE etl_schedules ADD COLUMN timeout_seconds INTEGER DEFAULT 3600 COMMENT '超时时间（秒）';
ALTER TABLE etl_schedules ADD COLUMN last_run_status TEXT COMMENT '最后执行状态';
ALTER TABLE etl_schedules ADD COLUMN last_run_duration INTEGER COMMENT '最后执行时长（秒）';
ALTER TABLE etl_schedules ADD COLUMN next_run_at TIMESTAMP COMMENT '下次执行时间';

CREATE INDEX IF NOT EXISTS idx_schedule_task ON etl_schedules(task_id);
CREATE INDEX IF NOT EXISTS idx_schedule_enabled ON etl_schedules(is_enabled);
CREATE INDEX IF NOT EXISTS idx_schedule_next_run ON etl_schedules(next_run_at);

-- ============================================
-- 8. 插入示例数据
-- ============================================

-- 示例数据源
INSERT OR IGNORE INTO etl_datasources (name, type, host, port, database, username, description) VALUES
('主业务数据库', 'mysql', 'localhost', 3306, 'business_db', 'root', '公司主营业务数据库'),
('数据仓库', 'mysql', 'localhost', 3306, 'data_warehouse', 'root', '企业数据仓库'),
('销售数据 CSV', 'csv', NULL, NULL, NULL, NULL, NULL, './data/sales_data.csv', NULL, '销售数据文件');

-- 示例转换任务
INSERT OR IGNORE INTO etl_transform_tasks (name, source_datasource_id, source_table, target_datasource_id, target_table, extract_mode, description) VALUES
('销售数据同步', 1, 'sales_orders', 2, 'ods_sales_orders', 'incremental', '从业务库同步销售订单到数仓'),
('客户数据清洗', 1, 'customers', 2, 'dwd_customers', 'full', '客户数据清洗和标准化'),
('产品数据聚合', 1, 'products', 2, 'dws_product_stats', 'full', '产品统计数据聚合');

-- ============================================
-- 9. 创建视图
-- ============================================

-- ETL 任务执行统计视图
CREATE VIEW IF NOT EXISTS v_etl_task_stats AS
SELECT 
    t.task_name,
    t.task_layer,
    COUNT(*) as total_runs,
    SUM(CASE WHEN t.status = 'success' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN t.status = 'failed' THEN 1 ELSE 0 END) as failed_count,
    AVG(t.duration_seconds) as avg_duration,
    MAX(t.start_time) as last_run_time,
    (SELECT error_message FROM etl_task_logs WHERE task_name = t.task_name ORDER BY start_time DESC LIMIT 1) as last_error
FROM etl_task_logs t
GROUP BY t.task_name, t.task_layer;

-- 数据源使用统计视图
CREATE VIEW IF NOT EXISTS v_datasource_usage AS
SELECT 
    d.id,
    d.name,
    d.type,
    d.is_enabled,
    COUNT(DISTINCT t.id) as task_count,
    MAX(l.start_time) as last_used_time
FROM etl_datasources d
LEFT JOIN etl_transform_tasks t ON d.id = t.source_datasource_id OR d.id = t.target_datasource_id
LEFT JOIN etl_task_logs l ON t.name = l.task_name
GROUP BY d.id, d.name, d.type, d.is_enabled;

-- ============================================
-- 迁移完成
-- ============================================

-- 验证迁移
SELECT '数据源表' as table_name, COUNT(*) as row_count FROM etl_datasources
UNION ALL
SELECT '转换任务表', COUNT(*) FROM etl_transform_tasks
UNION ALL
SELECT '任务依赖表', COUNT(*) FROM etl_task_dependencies
UNION ALL
SELECT '质量规则表', COUNT(*) FROM etl_quality_rules
UNION ALL
SELECT '质量检查结果表', COUNT(*) FROM etl_quality_check_results
UNION ALL
SELECT 'ETL 日志表', COUNT(*) FROM etl_task_logs
UNION ALL
SELECT '调度表', COUNT(*) FROM etl_schedules;
