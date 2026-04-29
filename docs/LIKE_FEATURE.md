# 点赞功能实现文档

## 功能概述

点赞功能是社交系统的核心功能之一，允许用户对内容（帖子、评论、报表）进行点赞操作。

## 技术栈

- **后端**: FastAPI (Python)
- **前端**: Vue 3 + Element Plus
- **数据库**: MySQL

## 数据库设计

### 点赞表 (likes)

```sql
CREATE TABLE likes (
    like_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '点赞用户 ID',
    target_type VARCHAR(50) NOT NULL COMMENT '目标类型：post-帖子，comment-评论，report-报表',
    target_id BIGINT NOT NULL COMMENT '目标 ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_target (user_id, target_type, target_id),
    INDEX idx_target (target_type, target_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='点赞表';
```

### 相关表字段更新

- `posts` 表：添加 `like_count` 字段
- `comments` 表：添加 `like_count` 字段
- `report_configs` 表：添加 `like_count` 字段

## 后端 API

### 文件位置
`/backend/api/likes.py`

### API 端点

| 方法 | 端点 | 描述 | 需要认证 |
|------|------|------|----------|
| POST | /api/likes | 点赞 | 是 |
| DELETE | /api/likes | 取消点赞 | 是 |
| GET | /api/likes/status | 获取点赞状态 | 是 |
| GET | /api/likes/count | 获取点赞数量 | 否 |
| GET | /api/likes/list | 获取点赞用户列表 | 否 |
| GET | /api/likes/my | 获取我的点赞列表 | 是 |

### 请求/响应示例

#### 点赞
```json
// 请求
POST /api/likes
{
  "target_type": "post",
  "target_id": 1
}

// 响应
{
  "success": true,
  "message": "点赞成功",
  "data": {
    "count": 10
  }
}
```

#### 取消点赞
```json
// 请求
DELETE /api/likes?target_type=post&target_id=1

// 响应
{
  "success": true,
  "message": "取消成功",
  "data": {
    "count": 9
  }
}
```

#### 获取点赞状态
```json
// 请求
GET /api/likes/status?target_type=post&target_id=1

// 响应
{
  "target_type": "post",
  "target_id": 1,
  "count": 10,
  "user_liked": true
}
```

## 前端组件

### 文件位置
`/frontend/src/components/LikeButton.vue`

### Props

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| targetType | String | 必填 | 目标类型 (post/comment/report) |
| targetId | Number/String | 必填 | 目标 ID |
| initialCount | Number | 0 | 初始点赞数 |
| initialLiked | Boolean | false | 是否已点赞 |
| disabled | Boolean | false | 是否禁用 |
| showCount | Boolean | true | 显示计数 |
| size | String | 'default' | 按钮大小 (large/default/small) |

### Events

| 事件名 | 参数 | 描述 |
|--------|------|------|
| like-change | {targetType, targetId, isLiked, count} | 点赞状态变化 |
| count-change | count | 计数变化 |

### 使用示例

```vue
<template>
  <LikeButton
    target-type="post"
    :target-id="1"
    :initial-count="10"
    :initial-liked="false"
    @like-change="onLikeChange"
  />
</template>

<script setup>
import LikeButton from '@/components/LikeButton.vue'

const onLikeChange = (data) => {
  console.log('点赞变化:', data)
}
</script>
```

## 测试

### 单元测试文件
`/backend/tests/test_likes.py`

### 测试覆盖
- [x] 点赞成功
- [x] 重复点赞处理
- [x] 取消点赞成功
- [x] 取消未点赞的内容
- [x] 获取点赞状态
- [x] 获取点赞数量（无需认证）
- [x] 无效目标类型处理
- [x] 获取点赞用户列表
- [x] 获取我的点赞列表

### 运行测试
```bash
cd erp-bi-system/backend
pytest tests/test_likes.py -v
```

## 测试页面

访问 `/admin/like-test` 可以查看点赞功能的测试页面。

## 下一步

点赞功能已完成，接下来可以实现：
1. **关注功能** - 用户可以关注其他用户
2. **评论功能** - 用户可以对内容发表评论
3. **通知功能** - 点赞、评论、关注等互动通知

## 迁移步骤

### 1. 执行数据库迁移
```bash
mysql -u root -p erp_bi < backend/migrations/004_add_social_features.sql
```

### 2. 重启后端服务
```bash
cd erp-bi-system/backend
python main.py
```

### 3. 访问测试页面
```
http://localhost:8001/admin/like-test
```
