-- AI数据融合平台后台管理数据库初始化脚本
-- MySQL 5.7+

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS erp_bi DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE erp_bi;

-- ===========================================
-- 用户表（扩展现有用户表）
-- ===========================================
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    real_name VARCHAR(50),
    role_id INT,
    status TINYINT DEFAULT 1 COMMENT '1-启用，0-禁用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 插入默认管理员用户
INSERT INTO users (username, password_hash, email, real_name, role_id, status)
VALUES ('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'admin@example.com', '系统管理员', 1, 1)
ON DUPLICATE KEY UPDATE username=username;

-- ===========================================
-- 角色表
-- ===========================================
CREATE TABLE IF NOT EXISTS roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_role_name (role_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- 插入默认角色
INSERT INTO roles (role_name, description) VALUES
('超级管理员', '系统最高权限角色'),
('管理员', '系统管理员，拥有大部分管理权限'),
('普通用户', '普通用户，只能查看报表'),
('数据分析师', '可以进行数据分析和 AI 问数')
ON DUPLICATE KEY UPDATE role_name=role_name;

-- ===========================================
-- 权限表
-- ===========================================
CREATE TABLE IF NOT EXISTS permissions (
    permission_id INT PRIMARY KEY AUTO_INCREMENT,
    permission_code VARCHAR(100) NOT NULL UNIQUE,
    permission_name VARCHAR(100) NOT NULL,
    resource_type VARCHAR(20) COMMENT 'menu-菜单，button-按钮，api-接口',
    parent_id INT DEFAULT 0 COMMENT '父权限 ID，用于树形结构',
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_parent (parent_id),
    INDEX idx_code (permission_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限表';

-- 插入默认权限（菜单树结构）
INSERT INTO permissions (permission_code, permission_name, resource_type, parent_id, sort_order) VALUES
-- 一级菜单
('admin', '后台管理', 'menu', 0, 1),
('admin:user', '用户管理', 'menu', 0, 2),
('admin:role', '角色管理', 'menu', 0, 3),
('admin:report', '报表管理', 'menu', 0, 4),
('admin:etl', 'ETL 管理', 'menu', 0, 5),
('admin:monitor', '运维监控', 'menu', 0, 6),

-- 用户管理权限
('admin:user:list', '查看用户列表', 'api', 2, 1),
('admin:user:create', '创建用户', 'button', 2, 2),
('admin:user:edit', '编辑用户', 'button', 2, 3),
('admin:user:delete', '删除用户', 'button', 2, 4),
('admin:user:reset_password', '重置密码', 'button', 2, 5),
('admin:user:toggle_status', '启用/禁用', 'button', 2, 6),

-- 角色管理权限
('admin:role:list', '查看角色列表', 'api', 3, 1),
('admin:role:create', '创建角色', 'button', 3, 2),
('admin:role:edit', '编辑角色', 'button', 3, 3),
('admin:role:delete', '删除角色', 'button', 3, 4),
('admin:role:permission', '分配权限', 'button', 3, 5),

-- 报表管理权限
('admin:report:list', '查看报表列表', 'api', 4, 1),
('admin:report:create', '创建报表', 'button', 4, 2),
('admin:report:edit', '编辑报表', 'button', 4, 3),
('admin:report:delete', '删除报表', 'button', 4, 4),
('admin:report:publish', '发布/取消发布', 'button', 4, 5),

-- ETL 管理权限
('admin:etl:list', '查看任务列表', 'api', 5, 1),
('admin:etl:run', '运行任务', 'button', 5, 2),
('admin:etl:log', '查看日志', 'button', 5, 3),
('admin:etl:schedule', '调度配置', 'button', 5, 4),

-- 运维监控权限
('admin:monitor:system', '系统信息', 'api', 6, 1),
('admin:monitor:service', '服务状态', 'api', 6, 2),
('admin:monitor:log', '系统日志', 'api', 6, 3),
('admin:monitor:metrics', '性能指标', 'api', 6, 4)
ON DUPLICATE KEY UPDATE permission_code=permission_code;

-- ===========================================
-- 角色权限关联表
-- ===========================================
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id),
    INDEX idx_permission (permission_id),
    CONSTRAINT fk_role FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    CONSTRAINT fk_permission FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限关联表';

-- 给超级管理员分配所有权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 1, permission_id FROM permissions
ON DUPLICATE KEY UPDATE role_id=role_id;

-- ===========================================
-- 报表配置表
-- ===========================================
CREATE TABLE IF NOT EXISTS report_configs (
    report_id INT PRIMARY KEY AUTO_INCREMENT,
    report_name VARCHAR(100) NOT NULL,
    report_type VARCHAR(50) NOT NULL COMMENT 'chart-图表，table-表格，kpi-指标',
    description VARCHAR(200),
    sql_query TEXT COMMENT 'SQL 查询语句',
    config_json JSON COMMENT '图表配置 JSON',
    status VARCHAR(20) DEFAULT 'draft' COMMENT 'draft-草稿，published-已发布，archived-已归档',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    published_at TIMESTAMP NULL,
    INDEX idx_status (status),
    INDEX idx_type (report_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报表配置表';

-- ===========================================
-- ETL 任务日志表
-- ===========================================
CREATE TABLE IF NOT EXISTS etl_task_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    task_name VARCHAR(100) NOT NULL,
    task_layer VARCHAR(20) COMMENT 'ODS/DWD/DWS/ADS',
    status VARCHAR(20) NOT NULL COMMENT 'running-运行中，success-成功，failed-失败',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    duration_seconds INT COMMENT '耗时（秒）',
    message TEXT COMMENT '日志消息',
    error_message TEXT COMMENT '错误信息',
    INDEX idx_task (task_name),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ETL 任务日志表';

-- ===========================================
-- ETL 调度配置表
-- ===========================================
CREATE TABLE IF NOT EXISTS etl_schedules (
    schedule_id INT PRIMARY KEY AUTO_INCREMENT,
    task_name VARCHAR(100) NOT NULL,
    cron_expression VARCHAR(50) NOT NULL COMMENT 'Cron 表达式',
    is_enabled TINYINT DEFAULT 1 COMMENT '是否启用',
    last_run_at TIMESTAMP NULL,
    next_run_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_enabled (is_enabled),
    INDEX idx_next_run (next_run_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ETL 调度配置表';

-- 插入默认调度配置
INSERT INTO etl_schedules (task_name, cron_expression, is_enabled) VALUES
('ODS 数据抽取', '0 2 * * *', 1),
('DWD 数据清洗', '0 3 * * *', 1),
('DWS 数据聚合', '0 4 * * *', 1),
('ADS 报表生成', '0 5 * * *', 1)
ON DUPLICATE KEY UPDATE task_name=task_name;

-- ===========================================
-- ETL 作业定义表
-- ===========================================
CREATE TABLE IF NOT EXISTS etl_jobs (
    job_id INT PRIMARY KEY AUTO_INCREMENT,
    job_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    layer VARCHAR(20) NOT NULL COMMENT 'ODS/DWD/DWS/ADS',
    script_path VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active' COMMENT 'active/running/paused',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_job_layer (layer),
    INDEX idx_job_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ETL 作业定义表';

INSERT INTO etl_jobs (job_name, description, layer, script_path, status) VALUES
('ODS 数据抽取', '从业务库抽取原始数据到 ODS 层', 'ODS', 'etl/extractors/ods_extractor.py', 'active'),
('DWD 数据清洗', '清洗和标准化 ODS 层数据', 'DWD', 'etl/transformers/dwd_cleaner.py', 'active'),
('DWS 数据聚合', '轻度聚合生成汇总数据', 'DWS', 'etl/transformers/dws_aggregator.py', 'active'),
('ADS 报表生成', '生成面向应用的报表指标', 'ADS', 'etl/loaders/ads_loader.py', 'active')
ON DUPLICATE KEY UPDATE job_name=job_name;

-- ===========================================
-- ETL 开发脚本表
-- ===========================================
CREATE TABLE IF NOT EXISTS dev_scripts (
    script_id INT PRIMARY KEY AUTO_INCREMENT,
    script_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    script_type VARCHAR(20) DEFAULT 'sql' COMMENT 'sql/python',
    content LONGTEXT,
    status VARCHAR(20) DEFAULT 'draft' COMMENT 'draft/published/archived',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_script_type (script_type),
    INDEX idx_script_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ETL 开发脚本表';

INSERT INTO dev_scripts (script_name, description, script_type, content, status) VALUES
('ODS 抽取模板', '简单 SQL 模板，适合做基础抽取预览', 'sql', 'SELECT * FROM re_units LIMIT 20', 'draft'),
('ODS 加载模板', '基础加载脚本占位内容', 'sql', 'INSERT INTO ods_room (...) SELECT ...', 'draft')
ON DUPLICATE KEY UPDATE script_name=script_name;

-- ===========================================
-- ETL 工作流表
-- ===========================================
CREATE TABLE IF NOT EXISTS etl_workflows (
    workflow_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    layer VARCHAR(20) NOT NULL,
    nodes JSON,
    connections JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_workflow_layer (layer)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ETL 工作流表';

-- ===========================================
-- ETL 工作流执行记录表
-- ===========================================
CREATE TABLE IF NOT EXISTS etl_executions (
    execution_id VARCHAR(64) PRIMARY KEY,
    workflow_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running' COMMENT 'running/success/failed',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    duration_seconds INT,
    variables JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_execution_workflow (workflow_id),
    INDEX idx_execution_status (status),
    INDEX idx_execution_start_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ETL 工作流执行记录表';

-- ===========================================
-- 系统日志表
-- ===========================================
CREATE TABLE IF NOT EXISTS system_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    log_level VARCHAR(20) DEFAULT 'INFO' COMMENT 'DEBUG/INFO/WARNING/ERROR',
    module VARCHAR(50) COMMENT '模块名称',
    action VARCHAR(100) COMMENT '操作动作',
    user_id INT,
    username VARCHAR(50),
    ip_address VARCHAR(50),
    message TEXT,
    request_data JSON,
    response_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_level (log_level),
    INDEX idx_module (module),
    INDEX idx_user (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统日志表';
