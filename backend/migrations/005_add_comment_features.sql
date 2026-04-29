-- 评论功能增强数据库迁移脚本
-- 添加评论点赞、回复等索引支持

-- ===========================================
-- 评论表索引增强
-- ===========================================

-- 为评论点赞数添加索引（用于排序）
ALTER TABLE comments ADD INDEX idx_like_count (like_count DESC);

-- 为评论创建时间添加复合索引（用于按目标查询 + 时间排序）
ALTER TABLE comments ADD INDEX idx_target_created (target_type, target_id, created_at DESC);

-- ===========================================
-- 确保 posts 表有 comment_count 字段
-- ===========================================

-- 如果 posts 表没有 comment_count 字段，则添加
ALTER TABLE posts ADD COLUMN IF NOT EXISTS comment_count INT DEFAULT 0 COMMENT '评论数' AFTER like_count;

-- 为 posts 表的 comment_count 添加索引
ALTER TABLE posts ADD INDEX idx_comment_count (comment_count DESC);

-- ===========================================
-- report_configs 表添加 comment_count 字段
-- ===========================================

-- 给报表配置表添加评论计数字段
ALTER TABLE report_configs ADD COLUMN IF NOT EXISTS comment_count INT DEFAULT 0 COMMENT '评论数' AFTER like_count;

-- 为 report_configs 表的 comment_count 添加索引
ALTER TABLE report_configs ADD INDEX idx_comment_count (comment_count DESC);
