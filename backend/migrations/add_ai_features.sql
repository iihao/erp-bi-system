-- AI数据融合平台数据库迁移脚本
-- 用于添加 AI 智能问数相关功能
-- 执行日期：2026-03-15

-- ============================================
-- 1. 用户表添加 AI 相关字段
-- ============================================

-- 添加 AI 问数权限字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_enabled TINYINT(1) DEFAULT 1 COMMENT 'AI 问数权限：1-启用，0-禁用';

-- 添加每日配额字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_quota INT DEFAULT 100 COMMENT '每日 AI 查询配额';

-- 添加今日已用字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_used_today INT DEFAULT 0 COMMENT '今日已用查询次数';

-- 为已有用户设置默认值
UPDATE users SET ai_enabled = 1, ai_quota = 100, ai_used_today = 0 WHERE ai_enabled IS NULL;

-- ============================================
-- 2. 创建 AI 查询日志表
-- ============================================

CREATE TABLE IF NOT EXISTS ai_query_logs (
    query_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '查询 ID',
    user_id INT NOT NULL COMMENT '用户 ID',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    question TEXT NOT NULL COMMENT '用户问题',
    sql TEXT COMMENT '生成的 SQL',
    status VARCHAR(20) NOT NULL COMMENT '状态：success/error',
    execution_time INT DEFAULT 0 COMMENT '执行时间 (ms)',
    result_count INT DEFAULT 0 COMMENT '结果数量',
    error_message TEXT COMMENT '错误信息',
    match_source VARCHAR(20) DEFAULT '' COMMENT '匹配来源：标准库命中/AI在线生成/错误',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_username (username),
    INDEX idx_status (status),
    INDEX idx_match_source (match_source),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 问数日志表';

-- ============================================
-- 3. 创建 AI 配置表（可选，使用文件存储时可省略）
-- ============================================

CREATE TABLE IF NOT EXISTS ai_config (
    config_id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(50) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    config_type VARCHAR(20) DEFAULT 'string' COMMENT '配置类型',
    description VARCHAR(200) COMMENT '配置说明',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by INT COMMENT '最后更新人 ID'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 配置表';

-- 插入默认配置
INSERT INTO ai_config (config_key, config_value, config_type, description) VALUES
    ('api_key', '', 'string', '百炼 API 密钥'),
    ('base_url', 'https://dashscope.aliyuncs.com/api/v1', 'string', 'API 地址'),
    ('model', 'qwen-plus', 'string', 'AI 模型'),
    ('daily_quota', '100', 'number', '每日默认配额'),
    ('sensitive_words', 'DROP,DELETE,TRUNCATE,GRANT,REVOKE', 'string', '敏感词列表'),
    ('sensitive_tables', 'users,roles,permissions,system_logs', 'string', '敏感表列表')
ON DUPLICATE KEY UPDATE config_key = config_key;

-- ============================================
-- 4. 创建系统日志表（如不存在）
-- ============================================

CREATE TABLE IF NOT EXISTS system_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    log_level VARCHAR(20) NOT NULL COMMENT '日志级别',
    module VARCHAR(50) COMMENT '模块',
    action VARCHAR(50) COMMENT '操作',
    username VARCHAR(50) COMMENT '用户',
    message TEXT COMMENT '消息内容',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统日志表';

-- ============================================
-- 5. 验证迁移结果
-- ============================================

-- 检查用户表字段
SELECT COLUMN_NAME, DATA_TYPE, COLUMN_DEFAULT, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'users'
  AND COLUMN_NAME IN ('ai_enabled', 'ai_quota', 'ai_used_today');

-- 检查表是否创建成功
SHOW TABLES LIKE 'ai_%';

-- ============================================
-- 迁移完成
-- ============================================
