# 发现页面功能文档

## 概述

发现页面是 AI数据融合平台中的内容探索中心，为用户提供热门内容推荐、个性化推荐、分类浏览和内容搜索功能。

## 功能特性

### 1. 推荐内容展示

#### 热门推荐
- 基于热度算法排序的内容列表
- 热度计算公式：`热度 = (点赞数 × 1 + 评论数 × 2 + 浏览数 × 0.1) × 时间衰减系数`
- 时间衰减系数采用半衰期机制（半衰期 7 天）

#### 个性化推荐
- 基于用户关注列表推荐内容
- 基于用户点赞历史推荐相似内容
- 混合热门内容确保推荐多样性

### 2. 内容分类

| 分类 | 说明 | 图标 |
|------|------|------|
| 全部 | 所有内容混合展示 | 📋 |
| 热门 | 按热度排序的内容 | 🔥 |
| 树洞 | 匿名发布的帖子 | 🌳 |
| 动态 | 用户发布的动态 | 💬 |
| 报表 | 数据报表 | 📊 |

### 3. 标签系统

- 热门标签展示
- 点击标签快速搜索
- 标签来源于报表分类和用户自定义

### 4. 搜索功能

- 支持关键词搜索帖子和报表
- 支持按内容类型筛选
- 支持按分类筛选
- 分页展示搜索结果

### 5. 无限滚动

- 滚动到底部自动加载更多
- 手动"加载更多"按钮
- 分页加载，每页 20 条内容

### 6. 内容卡片

每个内容卡片展示：
- 作者信息（头像、昵称）
- 内容类型标识（帖子/报表）
- 标题和摘要
- 互动数据（点赞数、评论数、浏览数）
- 发布时间（智能格式化）

## 技术实现

### 后端 API

#### 文件位置
```
backend/api/discovery.py
```

#### API 端点

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/discovery/recommend` | GET | 获取推荐内容 | 是 |
| `/api/discovery/hot` | GET | 获取热门内容 | 否 |
| `/api/discovery/search` | GET | 搜索内容 | 否 |
| `/api/discovery/categories` | GET | 获取分类列表 | 否 |
| `/api/discovery/tags` | GET | 获取标签列表 | 否 |
| `/api/discovery/feed` | GET | 获取信息流 | 是 |
| `/api/discovery/config` | GET | 获取推荐配置 | 否 |

#### 推荐算法

```python
def calculate_hot_score(like_count, comment_count, view_count, created_at):
    """
    计算内容热度分数

    算法：热度 = (点赞数 × 1 + 评论数 × 2 + 浏览数 × 0.1) × 时间衰减系数

    时间衰减系数 = 2^(-天数/半衰期)，半衰期设为 7 天
    """
    # 基础互动分数
    base_score = (
        like_count * 1.0 +      # 点赞权重
        comment_count * 2.0 +   # 评论权重（更高，因为评论代表深度互动）
        view_count * 0.1        # 浏览权重（较低）
    )

    # 时间衰减
    days_old = (datetime.now() - created_date).days
    decay_factor = math.pow(2, -days_old / 7)  # 7 天半衰期

    return base_score * decay_factor
```

#### 个性化推荐策略

1. **关注用户内容优先**：关注用户发布的内容权重 +50
2. **相似内容推荐**：基于用户点赞历史，推荐同分类内容
3. **热门内容补充**：混合当前热门内容，确保多样性

### 前端实现

#### 文件位置
```
frontend/src/views/admin/Discovery.vue
frontend/src/api/index.js (添加 discovery 模块)
```

#### 组件结构

```
Discovery.vue
├── 页面头部
│   ├── 标题和描述
│   └── 搜索框
├── 主内容区
│   ├── 左侧边栏
│   │   ├── 分类导航卡片
│   │   └── 热门标签卡片
│   └── 内容区域
│       ├── 标签页切换
│       │   ├── 为你推荐
│       │   ├── 热门
│       │   ├── 树洞
│       │   └── 报表
│       └── 内容列表
│           ├── 内容卡片
│           └── 加载更多
```

#### 状态管理

```javascript
// 使用 Vue 3 Composition API
const activeTab = ref('recommend')      // 当前标签页
const currentCategory = ref('all')      // 当前分类
const searchKeyword = ref('')           // 搜索关键词
const contentList = ref([])             // 内容列表
const loading = ref(false)              // 加载状态
const hasMore = ref(true)               // 是否有更多内容
const currentPage = ref(1)              // 当前页码
```

## 数据模型

### 内容项结构

```json
{
  "id": 1,
  "type": "post",
  "title": "帖子标题",
  "content": "内容摘要...",
  "author_id": 123,
  "author_name": "用户名",
  "author_avatar": "头像 URL",
  "like_count": 10,
  "comment_count": 5,
  "view_count": 100,
  "category": "dynamic",
  "tags": [],
  "created_at": "2026-03-22 10:00:00",
  "score": 25.5
}
```

### API 响应格式

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

## 单元测试

### 文件位置
```
backend/tests/test_discovery.py
```

### 测试覆盖

- ✅ 推荐内容获取
- ✅ 热门内容列表
- ✅ 搜索功能
- ✅ 分类列表
- ✅ 标签列表
- ✅ 信息流获取
- ✅ 推荐配置
- ✅ 热度分数计算
- ✅ 内容格式化

### 运行测试

```bash
cd erp-bi-system/backend
pytest tests/test_discovery.py -v
```

## 路由配置

### 前端路由

```javascript
{
  path: 'discovery',
  name: 'Discovery',
  component: () => import('@/views/admin/Discovery.vue'),
  meta: { title: '发现' }
}
```

### 后端路由注册

```python
from api.discovery import router as discovery_router
app.include_router(discovery_router)
```

## 使用示例

### 获取推荐内容

```javascript
// 个性化推荐
api.discovery.getRecommendations({
  limit: 20,
  personalized: true
})

// 热门推荐
api.discovery.getRecommendations({
  limit: 20,
  personalized: false
})
```

### 搜索内容

```javascript
api.discovery.search({
  keyword: '数据分析',
  content_type: 'all',
  page: 1,
  page_size: 20
})
```

### 获取分类和标签

```javascript
// 获取分类
api.discovery.getCategories()

// 获取热门标签
api.discovery.getTags({ limit: 15 })
```

## 性能优化

1. **分页加载**：每页 20 条，避免一次性加载过多数据
2. **热度缓存**：热门内容可以缓存，定期更新
3. **无限滚动**：滚动到底部自动加载，提升用户体验
4. **搜索优化**：数据库索引优化搜索性能

## 未来扩展

1. **协同过滤推荐**：基于用户行为相似性推荐
2. **内容标签化**：自动提取内容关键词作为标签
3. **推荐反馈**：收集用户对推荐内容的反馈，优化算法
4. **A/B 测试**：测试不同推荐策略的效果
5. **机器学习推荐**：使用 ML 模型预测用户兴趣

## 相关文件

- 后端 API: `backend/api/discovery.py`
- 前端页面：`frontend/src/views/admin/Discovery.vue`
- API 封装：`frontend/src/api/index.js`
- 单元测试：`backend/tests/test_discovery.py`
- 路由配置：`frontend/src/router/index.js`, `backend/main.py`

## 开发日志

- 2026-03-22: 完成发现页面功能实现
  - ✅ 后端 API 开发
  - ✅ 推荐算法实现（热度 + 时间）
  - ✅ 前端页面开发
  - ✅ 单元测试编写
  - ✅ 文档编写
