# 消息功能文档

## 概述

消息功能是 AI数据融合平台的核心社交功能之一，提供用户之间的私信通信、系统通知推送、互动提醒等功能。

## 功能特性

### 1. 私信功能

用户之间可以发送私人消息，支持：
- 发送/接收私信
- 私信会话管理
- 消息已读/未读状态
- 回复功能
- 删除功能（软删除）

### 2. 系统通知

管理员可以向用户或全体用户发送系统通知：
- 单用户通知
- 广播通知（全体用户）
- 优先级设置（low/normal/high/urgent）
- 来源追踪（关联具体业务）

### 3. 互动通知

自动推送用户互动相关的通知：
- 点赞通知
- 评论通知
- 关注通知
- 支持通知设置（用户可开关）

### 4. 消息管理

- 消息列表分页
- 按类型筛选（全部/私信/系统/互动）
- 批量标记已读
- 批量删除
- 一键已读
- 未读消息计数

### 5. 公告功能

- 发布公告
- 公告列表/详情
- 已读/未读追踪
- 查看统计

## 数据库设计

### 核心表结构

#### messages（消息主表）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| message_type | TEXT | 消息类型：private/system/interaction |
| sender_id | INTEGER | 发送者 ID |
| receiver_id | INTEGER | 接收者 ID |
| title | TEXT | 消息标题 |
| content | TEXT | 消息内容 |
| content_html | TEXT | HTML 格式内容 |
| source_type | TEXT | 来源类型：like/comment/follow/system |
| source_id | INTEGER | 来源 ID |
| source_url | TEXT | 来源链接 |
| is_read | INTEGER | 是否已读：0/1 |
| read_at | TIMESTAMP | 阅读时间 |
| deleted_by_sender | INTEGER | 发送者是否删除 |
| deleted_by_receiver | INTEGER | 接收者是否删除 |
| extra_json | TEXT | 扩展数据（JSON） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### message_conversations（私信会话表）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| user1_id | INTEGER | 会话参与者 1 |
| user2_id | INTEGER | 会话参与者 2 |
| last_message_id | INTEGER | 最后一条消息 ID |
| last_message_preview | TEXT | 最后消息预览 |
| last_message_time | TIMESTAMP | 最后消息时间 |
| unread_count_user1 | INTEGER | user1 未读数 |
| unread_count_user2 | INTEGER | user2 未读数 |
| deleted_by_user1 | INTEGER | user1 是否删除会话 |
| deleted_by_user2 | INTEGER | user2 是否删除会话 |

#### notification_settings（通知设置表）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 用户 ID |
| enable_like_notification | INTEGER | 点赞通知开关 |
| enable_comment_notification | INTEGER | 评论通知开关 |
| enable_follow_notification | INTEGER | 关注通知开关 |
| enable_system_notification | INTEGER | 系统通知开关 |
| notify_email | INTEGER | 邮件通知 |
| notify 站内 | INTEGER | 站内通知 |
| enable_digest | INTEGER | 启用日报汇总 |
| digest_time | TEXT | 日报发送时间 |

#### announcements（公告表）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| title | TEXT | 公告标题 |
| content | TEXT | 公告内容 |
| content_html | TEXT | HTML 格式内容 |
| status | TEXT | 状态：draft/published/archived |
| published_at | TIMESTAMP | 发布时间 |
| priority | TEXT | 优先级：low/normal/high/urgent |
| is_sticky | INTEGER | 是否置顶 |
| target_role_id | INTEGER | 目标角色 ID |
| target_user_ids | TEXT | 目标用户 IDs |
| view_count | INTEGER | 查看次数 |
| author_id | INTEGER | 作者 ID |

#### announcement_views（公告查看记录）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| announcement_id | INTEGER | 公告 ID |
| user_id | INTEGER | 用户 ID |
| viewed_at | TIMESTAMP | 查看时间 |

## API 接口

### 消息接口

#### 发送私信
```
POST /api/messages/send
Body: {
  "receiver_id": 2,
  "title": "消息标题",
  "content": "消息内容"
}
```

#### 获取消息列表
```
GET /api/messages/list
Params:
  - message_type: 消息类型（可选：private/system/interaction）
  - page: 页码（默认 1）
  - page_size: 每页数量（默认 20）
```

#### 获取私信会话列表
```
GET /api/messages/conversation/list
Params:
  - page: 页码
  - page_size: 每页数量
```

#### 获取会话消息记录
```
GET /api/messages/conversation/{user_id}
Params:
  - page: 页码
  - page_size: 每页数量
```

#### 获取消息详情
```
GET /api/messages/{message_id}
```

#### 批量标记已读
```
POST /api/messages/mark-read
Body: {
  "message_ids": [1, 2, 3],
  "operation": "read"
}
```

#### 标记为未读
```
POST /api/messages/mark-unread?message_id=1
```

#### 批量删除
```
POST /api/messages/delete
Body: {
  "message_ids": [1, 2, 3],
  "operation": "delete"
}
```

#### 一键已读
```
POST /api/messages/read-all
Params:
  - message_type: 消息类型（可选）
```

#### 获取未读数量
```
GET /api/messages/unread/count
Response: {
  "total": 5,
  "private": 2,
  "system": 1,
  "interaction": 2
}
```

#### 发送系统通知（管理员）
```
POST /api/messages/system-notify
Body: {
  "receiver_id": 0,  // 0 表示广播
  "title": "系统通知",
  "content": "通知内容",
  "priority": "normal",
  "source_type": "system",
  "source_id": null,
  "source_url": null
}
```

#### 发送互动通知
```
POST /api/messages/interaction-notify
Body: {
  "receiver_id": 2,
  "source_type": "like",  // like/comment/follow
  "source_id": 1,
  "content": "点赞了您的内容",
  "source_url": null
}
```

### 公告接口

#### 获取公告列表
```
GET /api/announcements/list
Params:
  - status_filter: 状态（默认 published）
  - page: 页码
  - page_size: 每页数量
```

#### 获取公告详情
```
GET /api/announcements/{announcement_id}
```

## 前端组件

### NotificationBadge.vue

消息通知徽章组件，显示未读消息数量。

```vue
<notification-badge
  icon="Bell"
  type="info"
  :circle="true"
  @click="handleClick"
/>
```

### Messages.vue

消息中心页面，包含：
- 消息类型切换（全部/私信/系统/互动）
- 消息列表
- 批量操作
- 写信对话框
- 回复对话框

访问路径：`/admin/messages`

## 使用示例

### 1. 发送私信

```javascript
// 前端调用
await this.$api.messages.send({
  receiver_id: 2,
  title: '合作邀请',
  content: '您好，想和您讨论一个合作项目...'
})
```

### 2. 获取未读消息数

```javascript
// 轮询未读消息数
async function fetchUnreadCount() {
  const response = await this.$api.messages.getUnreadCount()
  this.unreadCount = response.data.total
}

// 每 30 秒轮询一次
setInterval(fetchUnreadCount, 30000)
```

### 3. 批量标记已读

```javascript
// 选中多条消息后批量标记
await this.$api.messages.markAsRead([1, 2, 3, 4, 5])
```

### 4. 互动通知自动发送

```python
# 后端在点赞时自动发送通知
def like_target(user_id, target_type, target_id):
    # 执行点赞
    ...
    # 获取目标作者
    author_id = get_target_author(target_type, target_id)
    # 发送互动通知
    create_interaction_notification(
        receiver_id=author_id,
        sender_id=user_id,
        source_type="like",
        source_id=like_id,
        content="点赞了您的内容"
    )
```

## 注意事项

1. **消息删除**: 采用软删除机制，deleted_by_sender 和 deleted_by_receiver 分别标记
2. **会话唯一性**: user1_id 始终小于 user2_id，确保会话唯一性
3. **通知设置**: 用户可以关闭特定类型的互动通知
4. **权限控制**: 系统通知需要管理员权限
5. **未读计数**: 查看消息详情时自动标记为已读

## 扩展建议

1. **消息推送**: 集成 WebSocket 实现实时消息推送
2. **邮件通知**: 重要通知发送邮件提醒
3. **消息模板**: 系统通知使用模板，支持变量替换
4. **消息分类**: 进一步细分消息类别
5. **消息搜索**: 支持按关键词搜索历史消息
6. **消息置顶**: 重要消息可以置顶
7. **消息撤回**: 发送后一定时间内可撤回

## 相关文件

- 后端 API: `backend/api/messages.py`
- 数据库迁移：`backend/migrations/008_add_message_feature.sql`
- 前端页面：`frontend/src/views/admin/Messages.vue`
- 前端组件：`frontend/src/components/NotificationBadge.vue`
- 前端 API: `frontend/src/api/messages.js`
- 单元测试：`backend/tests/test_messages.py`
