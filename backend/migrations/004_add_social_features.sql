-- 社交功能数据库迁移脚本
-- 添加点赞、关注、评论功能支持

-- ===========================================
-- 点赞表
-- ===========================================
CREATE TABLE IF NOT EXISTS likes (
    like_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '点赞用户 ID',
    target_type VARCHAR(50) NOT NULL COMMENT '目标类型：post-帖子，comment-评论，report-报表',
    target_id BIGINT NOT NULL COMMENT '目标 ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_target (user_id, target_type, target_id),
    INDEX idx_target (target_type, target_id),
    INDEX idx_user (user_id),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_like_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='点赞表';

-- ===========================================
-- 关注表
-- ===========================================
CREATE TABLE IF NOT EXISTS follows (
    follow_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    follower_id INT NOT NULL COMMENT '关注者 ID',
    followed_id INT NOT NULL COMMENT '被关注者 ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_follower_followed (follower_id, followed_id),
    INDEX idx_follower (follower_id),
    INDEX idx_followed (followed_id),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_follower FOREIGN KEY (follower_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_followed FOREIGN KEY (followed_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='关注表';

-- ===========================================
-- 评论表
-- ===========================================
CREATE TABLE IF NOT EXISTS comments (
    comment_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '评论用户 ID',
    target_type VARCHAR(50) NOT NULL COMMENT '目标类型：post-帖子，report-报表',
    target_id BIGINT NOT NULL COMMENT '目标 ID',
    parent_id BIGINT DEFAULT 0 COMMENT '父评论 ID，用于回复评论',
    content TEXT NOT NULL COMMENT '评论内容',
    like_count INT DEFAULT 0 COMMENT '评论点赞数',
    status TINYINT DEFAULT 1 COMMENT '1-显示，0-隐藏',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_target (target_type, target_id),
    INDEX idx_user (user_id),
    INDEX idx_parent (parent_id),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_comment_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论表';

-- ===========================================
-- 帖子/内容表（用于树洞、动态等功能）
-- ===========================================
CREATE TABLE IF NOT EXISTS posts (
    post_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '作者 ID',
    title VARCHAR(200) COMMENT '标题',
    content TEXT NOT NULL COMMENT '内容',
    post_type VARCHAR(50) DEFAULT 'normal' COMMENT 'normal-普通，treehole-树洞（匿名）',
    like_count INT DEFAULT 0 COMMENT '点赞数',
    comment_count INT DEFAULT 0 COMMENT '评论数',
    view_count INT DEFAULT 0 COMMENT '浏览数',
    is_anonymous TINYINT DEFAULT 0 COMMENT '是否匿名',
    status TINYINT DEFAULT 1 COMMENT '1-公开，0-隐藏，-1-删除',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_type (post_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_post_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子/内容表';

-- ===========================================
-- 用户扩展表（添加个人主页相关字段）
-- ===========================================
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INT PRIMARY KEY,
    avatar_url VARCHAR(255) COMMENT '头像 URL',
    bio VARCHAR(500) COMMENT '个人简介',
    gender TINYINT DEFAULT 0 COMMENT '0-未知，1-男，2-女',
    birthday DATE COMMENT '生日',
    location VARCHAR(100) COMMENT '所在地',
    like_count INT DEFAULT 0 COMMENT '获得的点赞数',
    follower_count INT DEFAULT 0 COMMENT '粉丝数',
    following_count INT DEFAULT 0 COMMENT '关注数',
    post_count INT DEFAULT 0 COMMENT '帖子数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户扩展表';

-- ===========================================
-- 通知表（用于点赞、评论、关注等互动通知）
-- ===========================================
CREATE TABLE IF NOT EXISTS notifications (
    notification_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '接收通知的用户 ID',
    sender_id INT COMMENT '发送通知的用户 ID',
    notification_type VARCHAR(50) NOT NULL COMMENT 'like-点赞，follow-关注，comment-评论，reply-回复',
    target_type VARCHAR(50) COMMENT '目标类型',
    target_id BIGINT COMMENT '目标 ID',
    content TEXT COMMENT '通知内容',
    is_read TINYINT DEFAULT 0 COMMENT '是否已读',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_read (is_read),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_notification_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_notification_sender FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通知表';

-- ===========================================
-- 更新现有表添加点赞计数字段
-- ===========================================

-- 给报表配置表添加点赞计数字段
ALTER TABLE report_configs ADD COLUMN IF NOT EXISTS like_count INT DEFAULT 0 COMMENT '点赞数' AFTER status;
