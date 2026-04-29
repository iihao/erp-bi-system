# 树洞功能实现文档

## 功能概述

树洞功能为用户提供了一个匿名分享心事、吐槽、秘密的平台。用户发布的内容不会显示身份信息，但可以被其他用户点赞和评论。

## 特性

- **匿名发布**：发布树洞时不显示用户身份信息，统一显示为"匿名树洞"
- **点赞功能**：树洞可以被点赞，使用现有的点赞系统
- **评论功能**：树洞可以被评论，使用现有的评论系统
- **我的树洞**：用户可以查看自己发布的树洞（仅自己可见身份）
- **排序功能**：支持按时间/热度排序
- **敏感词过滤**：内置敏感词过滤机制，自动过滤不当内容

## 技术实现

### 1. 数据库设计

#### 主要表结构

树洞功能复用现有的 `posts` 表，通过 `post_type='treehole'` 标识树洞内容。

**posts 表（复用的表）**：
```sql
CREATE TABLE posts (
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

**sensitive_words 表（敏感词库）**：
```sql
CREATE TABLE sensitive_words (
    word_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    word VARCHAR(100) NOT NULL COMMENT '敏感词',
    category VARCHAR(50) DEFAULT 'general' COMMENT '分类',
    severity TINYINT DEFAULT 1 COMMENT '严重程度：1-低，2-中，3-高',
    is_active TINYINT DEFAULT 1 COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**post_views 表（浏览记录）**：
```sql
CREATE TABLE post_views (
    view_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    post_id BIGINT NOT NULL COMMENT '帖子 ID',
    user_id INT COMMENT '浏览用户 ID',
    ip_address VARCHAR(50) COMMENT 'IP 地址',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### 数据库迁移

执行迁移脚本：
```bash
mysql -u [username] -p [database_name] < backend/migrations/007_add_treehole_feature.sql
```

### 2. 后端 API

文件位置：`backend/api/treehole.py`

#### API 端点

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/treehole/list` | 获取树洞列表 | 是 |
| POST | `/api/treehole` | 发布树洞 | 是 |
| GET | `/api/treehole/{post_id}` | 获取树洞详情 | 是 |
| DELETE | `/api/treehole/{post_id}` | 删除树洞 | 是 |
| GET | `/api/treehole/my/list` | 获取我的树洞 | 是 |
| POST | `/api/treehole/reload-sensitive` | 重新加载敏感词 | 是 |

#### 请求/响应示例

**发布树洞**：
```http
POST /api/treehole
Content-Type: application/json
Authorization: Bearer {token}

{
    "title": "今天心情不太好",
    "content": "工作压力好大，想找个地方倾诉一下..."
}
```

响应：
```json
{
    "success": true,
    "message": "发布成功",
    "data": {
        "post_id": 1,
        "content": "工作压力好大，想找个地方倾诉一下...",
        "title": "今天心情不太好",
        "like_count": 0,
        "comment_count": 0,
        "view_count": 0,
        "is_anonymous": true,
        "display_username": "匿名树洞",
        "display_avatar": null,
        "created_at": "2026-03-22 10:00:00",
        "user_liked": false
    }
}
```

**获取树洞列表**：
```http
GET /api/treehole/list?page=1&page_size=20&sort_by=created_at
Authorization: Bearer {token}
```

响应：
```json
{
    "success": true,
    "message": "获取成功",
    "data": {
        "list": [...],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "has_more": true
    }
}
```

### 3. 前端实现

#### 组件结构

```
frontend/src/
├── api/
│   ├── index.js          # API 入口（添加 treehole 模块）
│   └── treehole.js       # 树洞 API 模块
├── components/
│   ├── ConfessionForm.vue    # 发布表单组件
│   └── ConfessionItem.vue    # 树洞项组件
└── views/
    └── admin/
        └── Treehole.vue      # 树洞页面
```

#### 主要组件

**ConfessionForm.vue** - 发布表单组件
- 标题输入（可选）
- 内容输入（必填，1-2000 字）
- 敏感词提示
- 发布按钮

**ConfessionItem.vue** - 树洞项组件
- 用户信息（匿名显示）
- 内容展示
- 点赞、评论、浏览统计
- 删除功能（仅作者）
- 评论区集成

**Treehole.vue** - 主页面
- 标签页切换（全部/热门/我的）
- 发布表单
- 树洞列表
- 分页功能

### 4. 路由配置

在 `frontend/src/router/index.js` 中添加：

```javascript
{
    path: 'treehole',
    name: 'AdminTreehole',
    component: () => import('@/views/admin/Treehole.vue'),
    meta: { title: '树洞' }
}
```

访问地址：`/admin/treehole`

### 5. 敏感词过滤

敏感词过滤在发布时自动执行：

- **高严重程度**：直接拒绝发布，返回错误信息
- **中低严重程度**：自动替换为 `***`

敏感词分类：
- `general` - 通用敏感词
- `ads` - 广告类
- `politics` - 政治类

管理员可通过 API 重新加载敏感词库：
```http
POST /api/treehole/reload-sensitive
Authorization: Bearer {token}
```

## 单元测试

测试文件：`backend/tests/test_treehole.py`

运行测试：
```bash
cd backend
pytest tests/test_treehole.py -v
```

或运行简单测试：
```bash
python tests/test_treehole.py
```

### 测试覆盖

- [x] 发布树洞成功
- [x] 发布无标题树洞
- [x] 发布空内容（验证失败）
- [x] 发布超长内容（验证失败）
- [x] 获取树洞列表
- [x] 获取热门树洞列表
- [x] 获取我的树洞列表
- [x] 获取树洞详情
- [x] 获取不存在的树洞（验证失败）
- [x] 删除树洞成功
- [x] 匿名显示验证
- [x] 点赞功能集成
- [x] 敏感词过滤

## 菜单集成

在后台管理系统中添加树洞菜单项：

1. 打开菜单配置文件（参考 `frontend/src/views/admin/MENU_CONFIG.md`）
2. 添加树洞菜单项到合适的分类下

示例配置：
```json
{
    "title": "树洞",
    "path": "/admin/treehole",
    "icon": "ChatDotSquare",
    "category": "社区"
}
```

## 部署说明

### 1. 数据库迁移

```bash
mysql -u root -p erp_bi < backend/migrations/007_add_treehole_feature.sql
```

### 2. 重启后端服务

```bash
cd backend
python main.py
```

### 3. 前端构建

```bash
cd frontend
npm run build
```

## API 集成说明

树洞功能与其他社交功能的集成：

1. **点赞集成**：使用现有的 `/api/likes` 接口，`target_type='post'`
2. **评论集成**：使用现有的 `/api/comments` 接口，`target_type='post'`
3. **个人主页**：树洞内容会在个人主页的"帖子"标签页中显示

## 注意事项

1. **匿名性**：树洞发布后，前端不显示作者信息，但数据库中仍保留 `user_id` 用于权限控制
2. **内容审核**：建议在管理后台添加内容审核功能
3. **浏览量统计**：使用 `post_views` 表记录浏览，防止重复计数
4. **敏感词维护**：定期更新敏感词库以应对新的不当内容

## 未来扩展

- [ ] 树洞分类/标签
- [ ] 树洞举报功能
- [ ] 管理员内容审核
- [ ] 树洞精选/推荐
- [ ] 表情包支持
- [ ] 图片上传支持

## 相关文件清单

### 后端
- `backend/api/treehole.py` - 树洞 API
- `backend/migrations/007_add_treehole_feature.sql` - 数据库迁移
- `backend/tests/test_treehole.py` - 单元测试
- `backend/main.py` - 路由注册（已修改）

### 前端
- `frontend/src/api/treehole.js` - 树洞 API 模块
- `frontend/src/api/index.js` - API 入口（已修改）
- `frontend/src/components/ConfessionForm.vue` - 发布表单
- `frontend/src/components/ConfessionItem.vue` - 树洞项
- `frontend/src/views/admin/Treehole.vue` - 树洞页面
- `frontend/src/router/index.js` - 路由配置（已修改）

### 文档
- `backend/docs/TREEHOLE_FEATURE.md` - 本文档

## 完成时间

2026-03-22
