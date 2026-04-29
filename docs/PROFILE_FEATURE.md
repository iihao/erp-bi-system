# 个人主页功能实现文档

## 概述

个人主页功能允许用户查看和编辑自己的个人资料，浏览其他用户的主页，查看用户发布的内容（帖子/报表）和点赞记录。

## 功能特性

### 1. 用户信息展示
- 头像显示（支持自定义 URL）
- 用户名
- 个人简介
- 性别
- 所在地
- 粉丝数、关注数、帖子数、获赞数统计

### 2. 用户内容展示
- **帖子列表**: 用户发布的所有帖子
- **报表列表**: 用户发布的所有报表
- **点赞记录**: 用户的点赞历史（仅自己可见）

### 3. 社交互动
- 关注/取消关注按钮（集成 FollowButton 组件）
- 粉丝/关注列表查看
- 点赞互动（集成 LikeButton 组件）

### 4. 个人资料编辑
- 仅自己的主页显示编辑入口
- 可编辑头像 URL、简介、性别、所在地

## 文件结构

```
erp-bi-system/
├── backend/
│   ├── api/
│   │   └── profile.py              # 个人主页 API
│   ├── migrations/
│   │   └── 006_add_profile_feature.sql  # 数据库迁移
│   ├── tests/
│   │   └── test_profile.py         # 单元测试
│   └── main.py                      # 需要注册路由
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── profile.js          # 个人主页 API 模块
│   │   │   └── index.js            # 已集成 profile API
│   │   ├── views/
│   │   │   └── Profile.vue         # 个人主页页面
│   │   └── router/
│   │       └── index.js            # 需要添加路由
│   └── src/components/
│       ├── FollowButton.vue        # 关注按钮组件 (已有)
│       └── LikeButton.vue          # 点赞按钮组件 (已有)
└── docs/
    └── PROFILE_FEATURE.md          # 本文档
```

## API 接口

### 获取用户资料
```
GET /api/profile/{user_id}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "admin",
    "avatar_url": "https://example.com/avatar.jpg",
    "bio": "个人简介",
    "gender": 1,
    "location": "北京",
    "follower_count": 10,
    "following_count": 5,
    "post_count": 20,
    "like_count": 100,
    "is_following": false,
    "is_me": true
  },
  "message": "获取成功"
}
```

### 获取当前用户资料
```
GET /api/profile
```

### 更新用户资料
```
PUT /api/profile
```

**请求体:**
```json
{
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "新的简介",
  "gender": 1,
  "location": "上海"
}
```

### 获取用户内容
```
GET /api/profile/{user_id}/posts
```

**查询参数:**
- `content_type`: 内容类型 (post/report)
- `page`: 页码
- `page_size`: 每页数量

### 获取用户点赞
```
GET /api/profile/{user_id}/likes
```

**查询参数:**
- `target_type`: 目标类型 (post/report/comment)
- `page`: 页码
- `page_size`: 每页数量

### 获取用户统计
```
GET /api/profile/{user_id}/stats
```

## 数据库表结构

### user_profiles (用户扩展表)
```sql
CREATE TABLE user_profiles (
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
```

### posts (帖子表)
```sql
CREATE TABLE posts (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200),
    content TEXT NOT NULL,
    post_type VARCHAR(50) DEFAULT 'normal',
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    status TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
```

## 前端组件

### Profile.vue
个人主页主组件，包含：
- 用户信息卡片
- 内容标签页（帖子/报表/点赞）
- 编辑资料对话框
- 粉丝/关注列表对话框

### 依赖的现有组件
- `FollowButton.vue`: 关注/取消关注按钮
- `LikeButton.vue`: 点赞/取消点赞按钮

## 路由配置

需要在 `frontend/src/router/index.js` 中添加：

```javascript
{
  path: '/profile',
  name: 'Profile',
  component: () => import('@/views/Profile.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/profile/:userId',
  name: 'UserProfile',
  component: () => import('@/views/Profile.vue'),
  meta: { requiresAuth: true }
}
```

## 后端路由注册

需要在 `backend/main.py` 中注册：

```python
from api.profile import router as profile_router

app.include_router(profile_router)
```

## 测试用例

测试文件：`backend/tests/test_profile.py`

### 测试覆盖
1. 获取用户资料成功/失败
2. 获取当前用户资料
3. 更新用户资料成功/失败
4. 获取用户帖子列表
5. 获取用户报表列表
6. 获取用户点赞列表
7. 获取用户统计信息
8. 权限验证（无认证访问）

### 运行测试
```bash
cd erp-bi-system/backend
pytest tests/test_profile.py -v
```

## 使用指南

### 访问自己的主页
1. 登录后访问 `/profile`
2. 或点击导航栏用户头像进入

### 访问他人主页
1. 访问 `/profile/{user_id}`
2. 从帖子/评论作者点击进入

### 编辑个人资料
1. 在自己的主页点击「编辑资料」按钮
2. 修改头像、简介、性别、所在地
3. 点击保存

### 关注/取消关注
1. 在他人主页点击「关注」按钮
2. 再次点击取消关注

### 查看粉丝/关注列表
1. 点击粉丝数或关注数
2. 在弹出的对话框中查看列表

## 响应式设计

个人主页页面支持响应式布局：
- 桌面端：完整布局
- 移动端：自适应单列布局

## 已知限制

1. 头像上传功能需要额外的文件存储服务支持
2. 帖子发布功能需要额外的帖子管理模块
3. 报表查看详情需要对应的报表详情页面

## 未来扩展

1. 头像上传功能
2. 个人主页主题自定义
3. 隐私设置（隐藏部分内容）
4. 个人成就/勋章展示
5. 活动记录时间线

## 更新日志

### v1.0.0 (2026-03-22)
- 初始版本发布
- 基础个人资料展示
- 用户内容浏览
- 关注/取消关注功能
- 点赞记录查看
