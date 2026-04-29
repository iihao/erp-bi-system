# 关注功能实现文档

## 功能概述

关注功能是社交系统的核心功能之一，允许用户关注其他用户，查看粉丝列表和关注列表，显示粉丝数和关注数。

## 技术栈

- **后端**: FastAPI (Python)
- **前端**: Vue 3 + Element Plus
- **数据库**: MySQL

## 数据库设计

### 关注表 (follows)

```sql
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
```

### 用户扩展表 (user_profiles)

```sql
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
```

## 后端 API

### 文件位置
`/backend/api/follows.py`

### API 端点

| 方法 | 端点 | 描述 | 需要认证 |
|------|------|------|----------|
| POST | /api/follows | 关注用户 | 是 |
| DELETE | /api/follows | 取消关注 | 是 |
| GET | /api/follows/status | 获取关注状态 | 是 |
| GET | /api/follows/count | 获取关注数量 | 否 |
| GET | /api/follows/followers | 获取粉丝列表 | 是 |
| GET | /api/follows/following | 获取关注列表 | 是 |
| GET | /api/follows/my | 获取我的关注/粉丝列表 | 是 |

### 请求/响应示例

#### 关注用户
```json
// 请求
POST /api/follows
{
  "followed_id": 1
}

// 响应
{
  "success": true,
  "message": "关注成功",
  "data": {
    "follower_count": 10,
    "following_count": 5
  }
}
```

#### 取消关注
```json
// 请求
DELETE /api/follows?followed_id=1

// 响应
{
  "success": true,
  "message": "取消成功",
  "data": {
    "follower_count": 9,
    "following_count": 4
  }
}
```

#### 获取关注状态
```json
// 请求
GET /api/follows/status?user_id=1

// 响应
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "张三",
    "avatar_url": "/avatars/1.jpg",
    "bio": "个人简介",
    "follower_count": 100,
    "following_count": 50,
    "is_following": true
  },
  "message": "获取成功"
}
```

#### 获取粉丝列表
```json
// 请求
GET /api/follows/followers?user_id=1&limit=20&offset=0

// 响应
{
  "success": true,
  "data": {
    "list": [
      {
        "user_id": 2,
        "username": "李四",
        "avatar_url": "/avatars/2.jpg",
        "bio": "简介",
        "follower_count": 30,
        "following_count": 20,
        "is_following": false,
        "created_at": "2026-03-20 10:00:00"
      }
    ],
    "total": 100
  },
  "message": "获取成功"
}
```

#### 获取关注列表
```json
// 请求
GET /api/follows/following?user_id=1&limit=20&offset=0

// 响应
{
  "success": true,
  "data": {
    "list": [
      {
        "user_id": 3,
        "username": "王五",
        "avatar_url": "/avatars/3.jpg",
        "bio": "简介",
        "follower_count": 50,
        "following_count": 40,
        "is_following": true,
        "created_at": "2026-03-19 15:30:00"
      }
    ],
    "total": 50
  },
  "message": "获取成功"
}
```

## 前端组件

### 文件位置
`/frontend/src/components/FollowButton.vue`

### Props

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| userId | Number/String | 必填 | 目标用户 ID |
| initialFollowing | Boolean | false | 是否已关注 |
| initialFollowerCount | Number | 0 | 初始粉丝数 |
| disabled | Boolean | false | 是否禁用 |
| showCount | Boolean | true | 显示粉丝数 |
| size | String | 'default' | 按钮大小 (large/default/small) |

### Events

| 事件名 | 参数 | 描述 |
|--------|------|------|
| follow-change | {userId, isFollowing, followerCount} | 关注状态变化 |
| count-change | count | 粉丝数变化 |

### Methods

| 方法名 | 参数 | 描述 |
|--------|------|------|
| refreshStatus | - | 刷新关注状态 |

### 使用示例

```vue
<template>
  <div class="user-card">
    <div class="user-info">
      <img :src="user.avatar" class="avatar" />
      <div class="user-details">
        <h3>{{ user.username }}</h3>
        <p>{{ user.bio }}</p>
        <div class="stats">
          <span class="stat">
            <strong>{{ stats.followerCount }}</strong> 粉丝
          </span>
          <span class="stat">
            <strong>{{ stats.followingCount }}</strong> 关注
          </span>
        </div>
      </div>
    </div>
    <FollowButton
      :user-id="user.id"
      :initial-following="user.isFollowing"
      :initial-follower-count="stats.followerCount"
      @follow-change="onFollowChange"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FollowButton from '@/components/FollowButton.vue'

const props = defineProps({
  user: Object
})

const stats = ref({
  followerCount: props.user.followerCount || 0,
  followingCount: props.user.followingCount || 0
})

const onFollowChange = (data) => {
  console.log('关注状态变化:', data)
  // 更新父组件中的状态
}
</script>
```

### 完整示例：个人主页

```vue
<template>
  <div class="user-profile">
    <!-- 用户信息卡片 -->
    <div class="profile-card">
      <img :src="userProfile.avatar_url" class="avatar-large" />
      <h2>{{ userProfile.username }}</h2>
      <p class="bio">{{ userProfile.bio || '暂无简介' }}</p>

      <!-- 统计信息 -->
      <div class="profile-stats">
        <div class="stat-item" @click="showFollowers = true">
          <span class="stat-value">{{ userProfile.follower_count }}</span>
          <span class="stat-label">粉丝</span>
        </div>
        <div class="stat-item" @click="showFollowing = true">
          <span class="stat-value">{{ userProfile.following_count }}</span>
          <span class="stat-label">关注</span>
        </div>
      </div>

      <!-- 关注按钮 -->
      <FollowButton
        v-if="currentUserId !== userProfile.user_id"
        :user-id="userProfile.user_id"
        :initial-following="userProfile.is_following"
        :initial-follower-count="userProfile.follower_count"
        @follow-change="handleFollowChange"
      />
    </div>

    <!-- 粉丝列表弹窗 -->
    <el-dialog v-model="showFollowers" title="粉丝列表">
      <el-table :data="followers">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="bio" label="简介" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <FollowButton
              v-if="row.user_id !== currentUserId"
              :user-id="row.user_id"
              :initial-following="row.is_following"
              size="small"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 关注列表弹窗 -->
    <el-dialog v-model="showFollowing" title="关注列表">
      <el-table :data="following">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="bio" label="简介" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <FollowButton
              v-if="row.user_id !== currentUserId"
              :user-id="row.user_id"
              :initial-following="row.is_following"
              size="small"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import FollowButton from '@/components/FollowButton.vue'
import api from '@/api'

const props = defineProps({
  userId: Number
})

const currentUserId = ref(parseInt(localStorage.getItem('user_id') || '0'))
const userProfile = ref({})
const followers = ref([])
const following = ref([])
const showFollowers = ref(false)
const showFollowing = ref(false)

// 加载用户资料
const loadUserProfile = async () => {
  try {
    const result = await api.follows.getStatus(props.userId)
    if (result.success) {
      userProfile.value = result.data
    }
  } catch (error) {
    ElMessage.error('加载用户资料失败')
  }
}

// 加载粉丝列表
const loadFollowers = async () => {
  try {
    const result = await api.follows.getFollowers(props.userId)
    if (result.success) {
      followers.value = result.data.list
    }
  } catch (error) {
    console.error('加载粉丝列表失败:', error)
  }
}

// 加载关注列表
const loadFollowing = async () => {
  try {
    const result = await api.follows.getFollowing(props.userId)
    if (result.success) {
      following.value = result.data.list
    }
  } catch (error) {
    console.error('加载关注列表失败:', error)
  }
}

// 处理关注状态变化
const handleFollowChange = (data) => {
  userProfile.value.is_following = data.isFollowing
  userProfile.value.follower_count = data.followerCount
}

onMounted(() => {
  loadUserProfile()
})
</script>
```

## API 客户端集成

### 文件位置
`/frontend/src/api/index.js`

### 使用方法

```javascript
import api from '@/api'

// 关注
await api.follows.follow({ followed_id: 1 })

// 取消关注
await api.follows.unfollow(1)

// 获取关注状态
const status = await api.follows.getStatus(1)

// 获取关注数量
const count = await api.follows.getCount(1)

// 获取粉丝列表
const followers = await api.follows.getFollowers(1, 20, 0)

// 获取关注列表
const following = await api.follows.getFollowing(1, 20, 0)

// 获取我的关注
const myFollowing = await api.follows.getMyFollows('following', 20, 0)

// 获取我的粉丝
const myFollowers = await api.follows.getMyFollows('followers', 20, 0)
```

## 测试

### 单元测试文件
`/backend/tests/test_follows.py`

### 测试覆盖
- [x] 关注成功
- [x] 关注自己（应失败）
- [x] 重复关注处理
- [x] 关注不存在的用户
- [x] 取消关注成功
- [x] 取消未关注的用户
- [x] 获取关注状态
- [x] 获取关注数量（无需认证）
- [x] 获取粉丝列表
- [x] 获取关注列表
- [x] 获取我的关注列表
- [x] 获取我的粉丝列表
- [x] 无效的列表类型处理

### 运行测试
```bash
cd erp-bi-system/backend
pytest tests/test_follows.py -v
```

## 错误码

| 错误码 | 描述 |
|--------|------|
| 4001 | 不能关注自己 |
| 4002 | 用户不存在 |
| 4003 | 已关注该用户 |
| 4004 | 尚未关注该用户 |
| 4005 | 无效的列表类型 |
| 5001 | 关注失败（服务器错误） |
| 5002 | 取消关注失败（服务器错误） |

## 通知功能

当用户关注其他用户时，系统会自动创建一条通知：

```python
create_notification(
    user_id=followed_id,      # 被关注者收到通知
    sender_id=follower_id,    # 关注者是发送者
    notification_type="follow",
    target_type=None,
    target_id=None,
    content="关注了您"
)
```

通知会存储在 `notifications` 表中，后续可以实现通知中心功能。

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

### 3. 重新构建前端（如有需要）
```bash
cd erp-bi-system/frontend
npm run build
```

## 与点赞功能的对比

| 特性 | 点赞功能 | 关注功能 |
|------|----------|----------|
| 目标对象 | 内容（帖子/评论/报表） | 用户 |
| 关系类型 | 用户对内容 | 用户对用户 |
| 取消操作 | 取消点赞 | 取消关注 |
| 通知 | 点赞通知 | 关注通知 |
| 列表展示 | 点赞用户列表 | 粉丝/关注列表 |
| 计数更新 | 目标内容点赞数 | 用户粉丝数/关注数 |

## 下一步

关注功能已完成，接下来可以实现：

1. **个人主页** - 展示用户信息、动态、作品等
2. **通知中心** - 集中展示点赞、关注、评论等互动通知
3. **评论功能** - 用户可以对内容发表评论
4. **动态/帖子** - 用户可以发布动态或帖子
5. **消息系统** - 用户之间的私信功能

## 相关文件清单

- 后端 API: `backend/api/follows.py`
- 前端组件：`frontend/src/components/FollowButton.vue`
- API 集成：`frontend/src/api/index.js`
- 单元测试：`backend/tests/test_follows.py`
- 数据库迁移：`backend/migrations/004_add_social_features.sql`
- 路由注册：`backend/main.py`
