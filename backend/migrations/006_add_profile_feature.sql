-- 个人主页功能数据库迁移脚本
-- 添加用户扩展表索引和 posts 表、report_configs 表支持

-- ============================================
-- SQLite 版本 - 个人主页功能支持
-- ============================================

-- ===========================================
-- 1. 确保 user_profiles 表存在（SQLite 兼容版本）
-- ===========================================

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY,
    avatar_url VARCHAR(255),
    bio VARCHAR(500),
    gender TINYINT DEFAULT 0,
    location VARCHAR(100),
    like_count INTEGER DEFAULT 0,
    follower_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    post_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ===========================================
-- 2. 确保 posts 表存在（SQLite 兼容版本）
-- ===========================================

CREATE TABLE IF NOT EXISTS posts (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200),
    content TEXT NOT NULL,
    post_type VARCHAR(50) DEFAULT 'normal',
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    is_anonymous INTEGER DEFAULT 0,
    status TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ===========================================
-- 3. 确保 likes 表存在（SQLite 兼容版本）
-- ===========================================

CREATE TABLE IF NOT EXISTS likes (
    like_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE (user_id, target_type, target_id)
);

-- ===========================================
-- 4. 确保 follows 表存在（SQLite 兼容版本）
-- ===========================================

CREATE TABLE IF NOT EXISTS follows (
    follow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower_id INTEGER NOT NULL,
    followed_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (follower_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (followed_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE (follower_id, followed_id)
);

-- ===========================================
-- 5. 确保 notifications 表存在（SQLite 兼容版本）
-- ===========================================

CREATE TABLE IF NOT EXISTS notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    sender_id INTEGER,
    notification_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    content TEXT,
    is_read INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ===========================================
-- 6. 创建索引以提升查询性能
-- ===========================================

-- user_profiles 表索引
CREATE INDEX IF NOT EXISTS idx_user_profiles_follower ON user_profiles(follower_count);
CREATE INDEX IF NOT EXISTS idx_user_profiles_following ON user_profiles(following_count);
CREATE INDEX IF NOT EXISTS idx_user_profiles_like ON user_profiles(like_count);

-- posts 表索引
CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_type ON posts(post_type);
CREATE INDEX IF NOT EXISTS idx_posts_like ON posts(like_count DESC);
CREATE INDEX IF NOT EXISTS idx_posts_comment ON posts(comment_count DESC);

-- likes 表索引
CREATE INDEX IF NOT EXISTS idx_likes_user ON likes(user_id);
CREATE INDEX IF NOT EXISTS idx_likes_target ON likes(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_likes_created ON likes(created_at DESC);

-- follows 表索引
CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_follows_followed ON follows(followed_id);
CREATE INDEX IF NOT EXISTS idx_follows_created ON follows(created_at DESC);

-- notifications 表索引
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);

-- report_configs 表索引（确保 created_by 字段有索引）
CREATE INDEX IF NOT EXISTS idx_report_configs_created_by ON report_configs(created_by);
CREATE INDEX IF NOT EXISTS idx_report_configs_status ON report_configs(status);

-- ============================================
-- 7. 初始化默认数据（可选）
-- ============================================

-- 为现有用户创建默认的 user_profiles 记录
INSERT OR IGNORE INTO user_profiles (user_id)
SELECT user_id FROM users;

-- ============================================
-- 验证表创建
-- ============================================

SELECT 'user_profiles' as table_name, COUNT(*) as row_count FROM user_profiles
UNION ALL
SELECT 'posts', COUNT(*) FROM posts
UNION ALL
SELECT 'likes', COUNT(*) FROM likes
UNION ALL
SELECT 'follows', COUNT(*) FROM follows
UNION ALL
SELECT 'notifications', COUNT(*) FROM notifications;
