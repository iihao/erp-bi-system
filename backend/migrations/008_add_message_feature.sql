-- AI数据融合平台消息功能迁移脚本
-- 创建时间：2026-03-22
-- 功能：私信、系统通知、互动通知支持

-- ============================================
-- 1. 消息主表（支持私信、系统通知、互动通知）
-- ============================================

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_type TEXT NOT NULL DEFAULT 'private' COMMENT '消息类型：private/system/interaction',

    -- 发送者信息
    sender_id INTEGER COMMENT '发送者 ID（系统消息为 NULL）',

    -- 接收者信息
    receiver_id INTEGER NOT NULL COMMENT '接收者 ID',

    -- 消息内容
    title TEXT NOT NULL COMMENT '消息标题',
    content TEXT NOT NULL COMMENT '消息内容',
    content_html TEXT COMMENT 'HTML 格式内容',

    -- 消息来源（用于互动通知）
    source_type TEXT COMMENT '来源类型：like/comment/follow/system',
    source_id INTEGER COMMENT '来源 ID（点赞 ID、评论 ID 等）',
    source_url TEXT COMMENT '来源链接',

    -- 消息状态
    is_read INTEGER DEFAULT 0 COMMENT '是否已读：0/1',
    read_at TIMESTAMP COMMENT '阅读时间',
    deleted_by_sender INTEGER DEFAULT 0 COMMENT '发送者是否删除',
    deleted_by_receiver INTEGER DEFAULT 0 COMMENT '接收者是否删除',

    -- 扩展字段
    extra_json TEXT COMMENT '扩展数据（JSON）',

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);
CREATE INDEX IF NOT EXISTS idx_messages_read ON messages(is_read);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_source ON messages(source_type, source_id);

-- ============================================
-- 2. 互动通知配置表
-- ============================================

CREATE TABLE IF NOT EXISTS notification_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,

    -- 互动通知开关
    enable_like_notification INTEGER DEFAULT 1 COMMENT '点赞通知开关',
    enable_comment_notification INTEGER DEFAULT 1 COMMENT '评论通知开关',
    enable_follow_notification INTEGER DEFAULT 1 COMMENT '关注通知开关',
    enable_system_notification INTEGER DEFAULT 1 COMMENT '系统通知开关',

    -- 通知方式
    notify_email INTEGER DEFAULT 0 COMMENT '邮件通知',
    notify站内 INTEGER DEFAULT 1 COMMENT '站内通知',

    -- 聚合设置
    enable_digest INTEGER DEFAULT 0 COMMENT '启用日报汇总',
    digest_time TEXT DEFAULT '09:00' COMMENT '日报发送时间',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_notification_user ON notification_settings(user_id);

-- ============================================
-- 3. 消息会话表（用于私信会话列表）
-- ============================================

CREATE TABLE IF NOT EXISTS message_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 会话参与者
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,

    -- 最新摘要
    last_message_id INTEGER COMMENT '最后一条消息 ID',
    last_message_preview TEXT COMMENT '最后消息预览',
    last_message_time TIMESTAMP COMMENT '最后消息时间',

    -- 未读数（各自维护）
    unread_count_user1 INTEGER DEFAULT 0 COMMENT 'user1 未读数',
    unread_count_user2 INTEGER DEFAULT 0 COMMENT 'user2 未读数',

    -- 删除状态
    deleted_by_user1 INTEGER DEFAULT 0,
    deleted_by_user2 INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user1_id) REFERENCES users(id),
    FOREIGN KEY (user2_id) REFERENCES users(id),

    UNIQUE(user1_id, user2_id)
);

CREATE INDEX IF NOT EXISTS idx_conversation_user1 ON message_conversations(user1_id);
CREATE INDEX IF NOT EXISTS idx_conversation_user2 ON message_conversations(user2_id);

-- ============================================
-- 4. 公告表
-- ============================================

CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL COMMENT '公告标题',
    content TEXT NOT NULL COMMENT '公告内容',
    content_html TEXT COMMENT 'HTML 格式内容',

    -- 发布状态
    status TEXT DEFAULT 'draft' COMMENT '状态：draft/published/archived',
    published_at TIMESTAMP COMMENT '发布时间',

    -- 优先级
    priority TEXT DEFAULT 'normal' COMMENT '优先级：low/normal/high/urgent',
    is_sticky INTEGER DEFAULT 0 COMMENT '是否置顶',

    -- 目标用户（NULL 表示全部）
    target_role_id INTEGER COMMENT '目标角色 ID',
    target_user_ids TEXT COMMENT '目标用户 IDs（逗号分隔）',

    -- 统计
    view_count INTEGER DEFAULT 0 COMMENT '查看次数',

    -- 作者
    author_id INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (author_id) REFERENCES users(id),
    FOREIGN KEY (target_role_id) REFERENCES roles(id)
);

CREATE INDEX IF NOT EXISTS idx_announcement_status ON announcements(status);
CREATE INDEX IF NOT EXISTS idx_announcement_priority ON announcements(priority);
CREATE INDEX IF NOT EXISTS idx_announcement_sticky ON announcements(is_sticky);
CREATE INDEX IF NOT EXISTS idx_announcement_published ON announcements(published_at);

-- ============================================
-- 5. 公告查看记录
-- ============================================

CREATE TABLE IF NOT EXISTS announcement_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    announcement_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (announcement_id) REFERENCES announcements(id),
    FOREIGN KEY (user_id) REFERENCES users(id),

    UNIQUE(announcement_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_announcement_view_ann ON announcement_views(announcement_id);
CREATE INDEX IF NOT EXISTS idx_announcement_view_user ON announcement_views(user_id);

-- ============================================
-- 6. 创建视图
-- ============================================

-- 用户未读消息数视图
CREATE VIEW IF NOT EXISTS v_user_unread_messages AS
SELECT
    receiver_id as user_id,
    COUNT(*) as total_unread,
    SUM(CASE WHEN message_type = 'private' THEN 1 ELSE 0 END) as private_unread,
    SUM(CASE WHEN message_type = 'system' THEN 1 ELSE 0 END) as system_unread,
    SUM(CASE WHEN message_type = 'interaction' THEN 1 ELSE 0 END) as interaction_unread
FROM messages
WHERE is_read = 0 AND deleted_by_receiver = 0
GROUP BY receiver_id;

-- 公告统计视图
CREATE VIEW IF NOT EXISTS v_announcement_stats AS
SELECT
    a.id,
    a.title,
    a.status,
    a.priority,
    a.is_sticky,
    a.view_count,
    COUNT(DISTINCT v.user_id) as unique_views,
    (SELECT COUNT(*) FROM users) as total_users,
    ROUND(COUNT(DISTINCT v.user_id) * 100.0 / (SELECT COUNT(*) FROM users), 2) as view_rate
FROM announcements a
LEFT JOIN announcement_views v ON a.id = v.announcement_id
GROUP BY a.id, a.title, a.status, a.priority, a.is_sticky, a.view_count;

-- ============================================
-- 7. 插入示例数据
-- ============================================

-- 默认通知设置（供参考，实际在用户创建时自动创建）
-- INSERT INTO notification_settings (user_id) SELECT id FROM users;

-- 示例公告
INSERT INTO announcements (title, content, status, priority, is_sticky, author_id, published_at) VALUES
('欢迎使用 AI数据融合平台', '欢迎来到 AI数据融合平台！这是一个集数据分析和商业智能于一体的平台。', 'published', 'normal', 1, 1, datetime('now')),
('系统维护通知', '系统将于本周日凌晨 2:00-4:00 进行例行维护，请提前保存数据。', 'published', 'high', 0, 1, datetime('now')),
('新功能上线：AI 智能查询', 'AI 智能查询功能已上线，支持自然语言生成 SQL 查询。', 'published', 'normal', 0, 1, datetime('now'));

-- ============================================
-- 8. 迁移完成验证
-- ============================================

SELECT '消息表' as table_name, COUNT(*) as row_count FROM messages
UNION ALL
SELECT '通知设置表', COUNT(*) FROM notification_settings
UNION ALL
SELECT '消息会话表', COUNT(*) FROM message_conversations
UNION ALL
SELECT '公告表', COUNT(*) FROM announcements
UNION ALL
SELECT '公告查看记录表', COUNT(*) FROM announcement_views;
