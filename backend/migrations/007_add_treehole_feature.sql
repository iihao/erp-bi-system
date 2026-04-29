-- 树洞功能数据库迁移脚本
-- 添加树洞（匿名发帖）功能支持

-- ===========================================
-- 敏感词库表（用于内容过滤）
-- ===========================================
CREATE TABLE IF NOT EXISTS sensitive_words (
    word_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    word VARCHAR(100) NOT NULL COMMENT '敏感词',
    category VARCHAR(50) DEFAULT 'general' COMMENT '分类：general-通用，politics-政治，ads-广告',
    severity TINYINT DEFAULT 1 COMMENT '严重程度：1-低，2-中，3-高',
    is_active TINYINT DEFAULT 1 COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_word (word),
    INDEX idx_category (category),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='敏感词库表';

-- ===========================================
-- 树洞表（基于 posts 表的专用视图/索引）
-- ===========================================
-- 注意：树洞数据存储在 posts 表中，post_type='treehole'
-- 这里创建索引以优化查询性能

-- 树洞专用索引
CREATE INDEX IF NOT EXISTS idx_posts_treehole ON posts(post_type, status, created_at);
CREATE INDEX IF NOT EXISTS idx_posts_treehole_hot ON posts(post_type, status, like_count, created_at);

-- ===========================================
-- 帖子浏览记录表（用于统计浏览量）
-- ===========================================
CREATE TABLE IF NOT EXISTS post_views (
    view_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    post_id BIGINT NOT NULL COMMENT '帖子 ID',
    user_id INT COMMENT '浏览用户 ID（匿名浏览时为 NULL）',
    ip_address VARCHAR(50) COMMENT 'IP 地址',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_post (post_id),
    INDEX idx_user (user_id),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_view_post FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子浏览记录表';

-- ===========================================
-- 更新 posts 表添加浏览次数唯一性约束
-- ===========================================
-- 防止同一用户重复刷浏览量（每天每用户每帖子只计一次）
ALTER TABLE post_views ADD UNIQUE INDEX uk_user_post_date (post_id, user_id, DATE(created_at));

-- ===========================================
-- 初始化敏感词数据（示例数据）
-- ===========================================
INSERT INTO sensitive_words (word, category, severity) VALUES
('广告', 'ads', 1),
('营销', 'ads', 1),
('赚钱', 'ads', 2),
('兼职', 'ads', 2),
('刷单', 'ads', 3),
('赌博', 'general', 3),
('色情', 'general', 3)
ON DUPLICATE KEY UPDATE word=word;

-- ===========================================
-- 创建树洞视图（方便查询）
-- ===========================================
CREATE OR REPLACE VIEW treehole_posts AS
SELECT
    p.post_id,
    p.content,
    p.title,
    p.like_count,
    p.comment_count,
    p.view_count,
    p.created_at,
    p.updated_at,
    p.status,
    p.is_anonymous,
    -- 匿名显示处理
    CASE
        WHEN p.is_anonymous = 1 THEN '匿名树洞'
        ELSE u.username
    END AS display_username,
    CASE
        WHEN p.is_anonymous = 1 THEN NULL
        ELSE u.avatar_url
    END AS display_avatar
FROM posts p
LEFT JOIN users u ON p.user_id = u.user_id
WHERE p.post_type = 'treehole' AND p.status = 1;
