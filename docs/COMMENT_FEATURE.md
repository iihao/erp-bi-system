# 评论功能文档

## 功能概述

评论功能允许用户对帖子 (post) 和报表 (report) 等内容发表评论，支持回复评论（嵌套评论）、编辑和删除自己的评论、评论点赞等功能。

## 主要特性

- ✅ 发布评论：用户可以对帖子或报表发表评论
- ✅ 回复评论：支持对评论进行回复，形成嵌套结构
- ✅ 编辑评论：用户可以编辑自己的评论
- ✅ 删除评论：用户可以删除自己的评论（软删除）
- ✅ 评论点赞：用户可以对评论进行点赞
- ✅ 分页加载：评论列表支持分页和排序
- ✅ 通知功能：评论和回复会通知相关内容作者

## 数据库设计

### 评论表 (comments)

```sql
CREATE TABLE comments (
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
    INDEX idx_like_count (like_count DESC),
    INDEX idx_target_created (target_type, target_id, created_at DESC),
    CONSTRAINT fk_comment_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
```

### 相关表更新

- `posts` 表添加 `comment_count` 字段
- `report_configs` 表添加 `comment_count` 字段
- `likes` 表支持 `target_type = 'comment'`

## API 接口

### 基础信息

- **基础路径**: `/api/comments`
- **认证方式**: Bearer Token
- **数据格式**: JSON

### 接口列表

#### 1. 创建评论

```http
POST /api/comments
Content-Type: application/json
Authorization: Bearer {token}

{
    "target_type": "post",      // 必填：post 或 report
    "target_id": 123,           // 必填：目标 ID
    "content": "评论内容",        // 必填：1-2000 字符
    "parent_id": 0              // 可选：父评论 ID，回复评论时使用
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "评论成功",
    "data": {
        "comment_id": 1,
        "user_id": 1,
        "username": "admin",
        "avatar_url": null,
        "target_type": "post",
        "target_id": 123,
        "parent_id": 0,
        "content": "评论内容",
        "like_count": 0,
        "reply_count": 0,
        "status": 1,
        "created_at": "2026-03-22 10:00:00",
        "updated_at": "2026-03-22 10:00:00",
        "user_liked": false
    }
}
```

#### 2. 获取评论列表

```http
GET /api/comments/list?target_type=post&target_id=123&page=1&page_size=20&sort_by=created_at
Authorization: Bearer {token}
```

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| target_type | string | 是 | - | 目标类型 (post/report) |
| target_id | integer | 是 | - | 目标 ID |
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页数量 (1-100) |
| sort_by | string | 否 | created_at | 排序字段 (created_at/like_count) |

**响应示例**:
```json
{
    "success": true,
    "data": {
        "list": [...],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "has_more": true
    },
    "message": "获取成功"
}
```

#### 3. 获取回复列表

```http
GET /api/comments/replies?parent_id=1&page=1&page_size=20
Authorization: Bearer {token}
```

#### 4. 获取评论详情

```http
GET /api/comments/{comment_id}
Authorization: Bearer {token}
```

#### 5. 编辑评论

```http
PUT /api/comments/{comment_id}
Content-Type: application/json
Authorization: Bearer {token}

{
    "content": "编辑后的内容"
}
```

#### 6. 删除评论

```http
DELETE /api/comments/{comment_id}
Authorization: Bearer {token}
```

**注意**: 删除为软删除，将 `status` 设置为 0

#### 7. 点赞评论

```http
POST /api/comments/{comment_id}/like
Authorization: Bearer {token}
```

#### 8. 取消点赞

```http
DELETE /api/comments/{comment_id}/like
Authorization: Bearer {token}
```

#### 9. 获取我的评论列表

```http
GET /api/comments/my/list?page=1&page_size=20&target_type=post
Authorization: Bearer {token}
```

## 前端组件

### CommentForm 组件

评论表单组件，用于发布和编辑评论。

```vue
<template>
  <CommentForm
    :target-type="targetType"
    :target-id="targetId"
    :parent-id="parentId"
    :comment-data="editData"
    :show-cancel="true"
    @submitted="handleSubmit"
    @cancelled="handleCancel"
  />
</template>
```

**Props**:
| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| targetType | string | 是 | - | 目标类型 |
| targetId | number | 是 | - | 目标 ID |
| parentId | number | 否 | 0 | 父评论 ID |
| commentData | object | 否 | null | 编辑的评论数据 |
| rows | number | 否 | 3 | 文本框行数 |
| showCancel | boolean | 否 | false | 显示取消按钮 |
| placeholder | string | 否 | '写下你的评论...' | 占位符 |

**Events**:
| 事件 | 参数 | 说明 |
|------|------|------|
| submitted | comment | 提交成功 |
| cancelled | - | 取消操作 |

### CommentItem 组件

单个评论项组件，显示评论内容和操作按钮。

```vue
<template>
  <CommentItem
    :comment="comment"
    :target-type="targetType"
    :target-id="targetId"
    :currentUserId="currentUserId"
    :is-reply="false"
    @reply="handleReply"
    @edit="handleEdit"
    @delete="handleDelete"
    @like="handleLike"
  />
</template>
```

### CommentList 组件

评论列表组件，包含评论表单和列表展示。

```vue
<template>
  <CommentList
    :target-type="targetType"
    :target-id="targetId"
    :show-form="true"
    :currentUserId="userId"
    @comment-count-change="handleCountChange"
  />
</template>
```

**使用示例**:

```vue
<template>
  <div class="post-detail">
    <div class="post-content">
      <!-- 帖子内容 -->
    </div>

    <div class="post-comments">
      <h3>评论 ({{ commentCount }})</h3>
      <CommentList
        target-type="post"
        :target-id="postId"
        :currentUserId="userId"
        @comment-count-change="commentCount = $event"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CommentList from '@/components/CommentList.vue'

const postId = ref(123)
const userId = ref(1)
const commentCount = ref(0)
</script>
```

## 单元测试

运行评论功能测试：

```bash
cd erp-bi-system/backend
pytest tests/test_comments.py -v
```

**测试覆盖**:
- ✅ 创建评论成功
- ✅ 无效目标类型
- ✅ 目标不存在
- ✅ 空内容验证
- ✅ 创建回复成功
- ✅ 父评论不存在
- ✅ 获取评论列表
- ✅ 评论分页
- ✅ 获取回复列表
- ✅ 编辑评论成功
- ✅ 编辑他人评论（无权限）
- ✅ 删除评论成功
- ✅ 删除他人评论（无权限）
- ✅ 点赞评论成功
- ✅ 重复点赞
- ✅ 取消点赞成功
- ✅ 取消未点赞评论
- ✅ 获取评论详情
- ✅ 获取我的评论列表

## 注意事项

1. **权限控制**: 用户只能编辑和删除自己的评论
2. **软删除**: 删除评论时将 `status` 设置为 0，保留数据完整性
3. **嵌套层级**: 当前支持一级回复（父评论 + 子回复）
4. **内容长度**: 评论内容限制在 1-2000 字符
5. **通知功能**: 评论和回复会自动通知相关内容作者
6. **计数同步**: 评论删除时会同步更新目标的 `comment_count`

## 后续优化建议

1. 支持多层嵌套回复（目前仅支持一级回复）
2. 添加评论举报功能
3. 添加评论审核功能（管理员可隐藏不当评论）
4. 支持评论富文本格式（@提及用户、表情等）
5. 添加评论搜索功能
6. 实现评论缓存优化性能

## 相关文件

- 后端 API: `backend/api/comments.py`
- 数据库迁移：`backend/migrations/005_add_comment_features.sql`
- 前端组件：
  - `frontend/src/components/CommentForm.vue`
  - `frontend/src/components/CommentItem.vue`
  - `frontend/src/components/CommentList.vue`
- 前端 API: `frontend/src/api/comments.js`
- 单元测试：`backend/tests/test_comments.py`
