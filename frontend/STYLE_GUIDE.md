# AI数据融合平台前端样式规范

## 设计系统

### 设计令牌 (Design Tokens)

所有样式应优先使用 `design-tokens.css` 中定义的 CSS 变量：

```css
/* 颜色 */
--primary, --primary-dark, --primary-light
--text-primary, --text-secondary, --text-tertiary
--bg-body, --bg-surface, --bg-surface-secondary
--border-light, --border, --border-dark

/* 间距 */
--spacing-1 (4px), --spacing-2 (8px), --spacing-3 (12px)
--spacing-4 (16px), --spacing-5 (20px), --spacing-6 (24px)
--spacing-8 (32px), --spacing-10 (40px), --spacing-12 (48px)

/* 圆角 */
--radius-none, --radius-sm, --radius, --radius-md
--radius-lg, --radius-xl, --radius-2xl, --radius-full

/* 阴影 */
--shadow-xs, --shadow-sm, --shadow, --shadow-md
--shadow-lg, --shadow-xl, --shadow-2xl

/* 字体 */
--text-xs, --text-sm, --text-base, --text-lg, --text-xl
--font-normal, --font-medium, --font-semibold, --font-bold

/* 动画 */
--transition-fast (150ms), --transition (200ms), --transition-slow (300ms)
--transition-cubic: cubic-bezier(0.4, 0, 0.2, 1)
```

### 动画效果

使用 `animations.css` 中预定义的动画类：

```css
/* 淡入动画 */
.animate-fade-in
.animate-fade-in-up
.animate-fade-in-down

/* 过渡效果 */
.transition-all
.transition-colors
.transition-transform
.transition-shadow

/* 特殊动画 */
.animate-spin (加载旋转)
.animate-pulse (脉冲效果)
.animate-shimmer (骨架屏)
```

## 布局规范

### 管理后台布局 (admin/Layout.vue)

```
┌─────────────────────────────────────┐
│ Sidebar │ Header                    │
│         ├───────────────────────────┤
│ 260px   │ Content                   │
│         │                           │
│         │                           │
└─────────┴───────────────────────────┘
```

**特性：**
- 侧边栏可折叠（260px → 64px）
- 响应式设计（移动端隐藏侧边栏）
- 顶部导航栏包含：面包屑、全局搜索、通知中心、用户菜单
- 内容区页面过渡动画

### 前台布局 (portal/Layout.vue)

```
┌─────────────────────────────────────┐
│ Sidebar │ Header                    │
│         ├───────────────────────────┤
│ 260px   │ Content (卡片化布局)      │
│         │                           │
└─────────┴───────────────────────────┘
```

**特性：**
- 侧边栏分组菜单 + 快捷入口
- 顶部栏显示用户信息和角色徽章
- 内容区卡片化布局

## 列表页规范

### 页面结构

```vue
<template>
  <div class="page-container">
    <!-- 1. 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">标题</h1>
      <p class="page-description">描述</p>
    </div>

    <!-- 2. 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :inline="true">
        <!-- 搜索框、筛选器、操作按钮 -->
      </el-form>
    </el-card>

    <!-- 3. 数据表格区 -->
    <el-card class="table-card">
      <!-- 工具栏 -->
      <div class="table-toolbar">...</div>
      
      <!-- 表格 -->
      <el-table>...</el-table>
      
      <!-- 分页 -->
      <div class="table-pagination">...</div>
    </el-card>
  </div>
</template>
```

### 表格样式要点

```css
/* 表头样式 */
.data-table :deep(.el-table__header th) {
  background: linear-gradient(135deg, var(--slate-100) 0%, var(--slate-50) 100%);
  font-weight: var(--font-semibold);
  padding: 14px 16px;
}

/* 行悬停效果 */
.data-table :deep(.el-table__body tr:hover) {
  background-color: var(--primary-50) !important;
}

/* 斑马纹 */
.data-table :deep(.el-table__row--striped td) {
  background: var(--slate-50);
}

/* 操作按钮 */
.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: var(--font-medium);
}
```

### 分页器样式

```css
.pagination :deep(.el-pager li.active) {
  background: var(--primary);
  color: #ffffff;
}

.pagination :deep(.el-pager li:hover) {
  background: var(--primary-50);
  color: var(--primary);
}
```

## 组件使用规范

### ProList 通用列表组件

```vue
<template>
  <ProList
    title="用户管理"
    description="管理系统用户账号"
    :data="users"
    :loading="loading"
    :total="total"
    v-model:current-page="page"
    v-model:page-size="pageSize"
    @refresh="loadData"
  >
    <!-- 搜索区 -->
    <template #search>
      <el-form :inline="true">
        <el-form-item label="关键词">
          <el-input v-model="keyword" />
        </el-form-item>
      </el-form>
    </template>

    <!-- 表格列 -->
    <el-table-column prop="name" label="姓名" />
    
    <!-- 工具栏右侧 -->
    <template #toolbar-right>
      <el-button @click="handleExport">导出</el-button>
    </template>
  </ProList>
</template>
```

## 图标使用

### SVG 图标规范

```vue
<svg class="icon-name" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <path d="..." stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

**常用尺寸：**
- 小图标：14px × 14px (按钮内)
- 中图标：18px × 18px (表头、菜单)
- 大图标：24px × 24px (独立按钮)
- 标题图标：28px × 28px (页面标题)

## 响应式断点

```css
/* 移动端 */
@media (max-width: 768px) {
  /* 侧边栏隐藏，显示汉堡菜单 */
  /* 表格工具栏垂直排列 */
  /* 分页器垂直排列 */
}

/* 平板 */
@media (max-width: 1024px) {
  /* 搜索框缩小 */
  /* KPI 卡片调整布局 */
}

/* 桌面 */
@media (min-width: 1025px) {
  /* 完整布局 */
}
```

## 颜色使用场景

| 颜色 | 用途 |
|------|------|
| `--primary` | 主操作按钮、链接、激活状态 |
| `--success` | 成功状态、启用标签 |
| `--warning` | 警告操作、待处理状态 |
| `--danger` | 删除操作、错误状态、禁用标签 |
| `--info` | 信息提示、普通标签 |

## 代码示例

### 完整的列表页模板

```vue
<template>
  <div class="page-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <svg class="title-icon" viewBox="0 0 24 24">...</svg>
          页面标题
        </h1>
        <p class="page-description">页面描述</p>
      </div>
    </div>

    <!-- 搜索区 -->
    <el-card class="search-card" shadow="sm">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="请输入" />
        </el-form-item>
        <el-form-item class="form-actions">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleCreate">新增</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格区 -->
    <el-card class="table-card" shadow="sm">
      <div class="table-toolbar">
        <div class="toolbar-left">
          <span class="toolbar-title">数据列表</span>
          <el-tag type="info">共 {{ total }} 条</el-tag>
        </div>
        <div class="toolbar-right">
          <el-button @click="loadData" :loading="loading" circle>
            <svg class="btn-icon" :class="{ 'spinning': loading }">...</svg>
          </el-button>
        </div>
      </div>

      <el-table :data="data" v-loading="loading" border stripe>
        <el-table-column type="selection" width="50" />
        <el-table-column prop="name" label="名称" sortable />
        <el-table-column label="操作" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
/* 使用 design-tokens.css 变量 */
.page-container {
  max-width: 100%;
}

.page-header {
  margin-bottom: var(--spacing-6);
}

/* ... 其他样式参考 design-tokens.css ... */
</style>
```

## 最佳实践

1. **始终使用 CSS 变量** - 不要硬编码颜色、间距等值
2. **保持一致的间距** - 使用 8px 基准网格系统
3. **添加适当的过渡** - 所有交互元素添加 `transition` 属性
4. **考虑响应式** - 移动优先，逐步增强
5. **使用语义化类名** - `.page-header`, `.table-toolbar`, `.action-btn`
6. **图标与文字对齐** - 使用 `display: flex; align-items: center; gap`
7. **加载状态** - 表格使用 `v-loading`，按钮使用 `:loading`
8. **错误处理** - 使用 ElMessage 和 ElMessageBox

## 文件结构

```
src/
├── styles/
│   ├── design-tokens.css      # 设计令牌（必须使用）
│   ├── animations.css         # 动画效果
│   ├── components.css         # 组件样式
│   └── global.css             # 全局样式
├── components/
│   ├── ProList.vue            # 通用列表组件
│   └── ...
└── views/
    ├── admin/
    │   ├── Layout.vue         # 管理后台布局
    │   ├── Dashboard.vue      # 管理后台首页
    │   ├── Users.vue          # 用户管理（示例）
    │   └── ...
    └── portal/
        ├── Layout.vue         # 前台布局
        └── ...
```
