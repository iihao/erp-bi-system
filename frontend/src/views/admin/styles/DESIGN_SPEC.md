# Admin 后台管理页面视觉统一规范

## 概述

本文档定义了 AI数据融合平台后台管理页面的统一视觉规范，确保所有页面具有一致、专业的外观和用户体验。

## 设计原则

1. **专业性** - 参考 SAP、Oracle 等企业级软件的设计风格
2. **一致性** - 所有页面使用统一的组件样式和交互规范
3. **高效性** - 清晰的视觉层次，减少认知负担
4. **可扩展性** - 模块化设计，便于新增功能

## 色彩系统

### 主色调
| 变量 | 色值 | 用途 |
|------|------|------|
| `--primary-50` | #eff6ff | 背景高亮 |
| `--primary-100` | #dbeafe | 标签背景 |
| `--primary-500` | #3b82f6 | 次要按钮 |
| `--primary-600` | #2563eb | 主要按钮 |
| `--primary-700` | #1d4ed8 | 按钮悬停 |

### 功能色
| 类型 | 背景色 | 文字色 | 用途 |
|------|--------|--------|------|
| 成功 | #dcfce7 | #166534 | 成功状态、启用标签 |
| 警告 | #fef3c7 | #92400e | 警告提示、禁用操作 |
| 危险 | #fee2e2 | #991b1b | 删除操作、错误状态 |
| 信息 | #dbeafe | #1e40af | 信息提示、普通标签 |

### 中性色
| 变量 | 色值 | 用途 |
|------|------|------|
| `--slate-50` | #f8fafc | 页面背景 |
| `--slate-100` | #f1f5f9 | 卡片背景 |
| `--slate-200` | #e2e8f0 | 边框颜色 |
| `--slate-500` | #64748b | 次要文字 |
| `--slate-600` | #475569 | 常规文字 |
| `--slate-900` | #1e293b | 主要文字 |

## 组件规范

### 卡片 (Card)
```css
- 圆角：12px
- 边框：1px solid #e2e8f0
- 阴影：0 1px 3px rgba(0,0,0,0.05)
- 悬停阴影：0 4px 12px rgba(0,0,0,0.08)
- 头部背景：linear-gradient(135deg, #f8fafc, #ffffff)
- 内边距：20px
```

### 表格 (Table)
```css
- 字体大小：13px
- 表头背景：linear-gradient(135deg, #f1f5f9, #f8fafc)
- 表头文字：#475569, 字重 600
- 表头内边距：12px 14px
- 单元格内边距：10px 14px
- 悬停背景：#eff6ff
- 斑马纹背景：#fafafa
- 边框颜色：#f1f5f9
```

### 按钮 (Button)
```css
- 圆角：8px
- 字重：500
- 字体大小：13px
- 内边距：8px 16px
- 悬停效果：上移 1px + 阴影
- 渐变方向：135deg
```

#### 按钮类型
| 类型 | 渐变起始 | 渐变结束 |
|------|----------|----------|
| Primary | #3b82f6 | #2563eb |
| Success | #10b981 | #059669 |
| Warning | #f59e0b | #d97706 |
| Danger | #ef4444 | #dc2626 |

### 标签 (Tag)
```css
- 圆角：6px
- 字重：500
- 字体大小：12px
- 内边距：4px 10px
- 无边框
```

### 对话框 (Dialog)
```css
- 圆角：16px
- 阴影：0 25px 50px -12px rgba(0,0,0,0.25)
- 头部背景：linear-gradient(135deg, #f8fafc, #ffffff)
- 头部内边距：20px 24px
- 身体内边距：24px
- 底部背景：#f8fafc
```

### 输入框 (Input)
```css
- 圆角：8px
- 边框：1px solid #e2e8f0
- 内边距：8px 12px
- 悬停边框：#cbd5e1
- 聚焦边框：#3b82f6 + 2px rgba(59,130,246,0.15) 阴影
```

## 布局规范

### 页面容器
```css
- 最大宽度：1600px
- 居中：margin auto
- 内边距：24px
- 背景色：#f8fafc
```

### 侧边栏
```css
- 展开宽度：260px
- 收起宽度：64px
- 背景：linear-gradient(180deg, var(--bg-sidebar), var(--bg-sidebar-dark))
- 菜单项高度：40px (一级) / 32px (二级)
- 选中背景：linear-gradient(135deg, rgba(59,130,246,0.2), rgba(37,99,235,0.1))
```

### 顶部导航
```css
- 高度：64px
- 背景：#ffffff
- 边框：1px solid #e2e8f0
- 内边距：0 24px
```

## 交互规范

### 悬停效果
- 卡片/按钮：上移 1px + 阴影加深
- 链接/文字：颜色变深或添加下划线
- 菜单项：背景色变亮

### 点击效果
- 按钮：回弹效果（移除上移）
- 链接按钮：无位移，仅颜色变化

### 加载状态
- 遮罩背景：rgba(255,255,255,0.8) + 4px 模糊
- 加载图标颜色：#3b82f6
- 加载文字：#475569

## 间距系统

基于 8px 网格系统：
- `--spacing-1`: 4px
- `--spacing-2`: 8px
- `--spacing-3`: 12px
- `--spacing-4`: 16px
- `--spacing-5`: 20px
- `--spacing-6`: 24px
- `--spacing-8`: 32px

## 字体系统

```css
--text-sm: 13px    /* 辅助文字、标签 */
--text-base: 14px  /* 正文字体 */
--text-lg: 16px    /* 标题字体 */
--text-xl: 18px    /* 大标题 */

--font-normal: 400
--font-medium: 500
--font-semibold: 600
--font-bold: 700
```

## 动画系统

```css
--transition-fast: 150ms
--transition: 200ms
--transition-slow: 300ms
--transition-cubic: cubic-bezier(0.4, 0, 0.2, 1)
```

## 使用方式

### 在 Vue 组件中使用

1. 自动应用（通过 Layout.vue 导入）：
```vue
<template>
  <div class="admin-page">
    <el-card>...</el-card>
    <el-table>...</el-table>
  </div>
</template>
```

2. 需要时可直接引用工具类：
```vue
<template>
  <div class="flex flex-between mb-4">
    <span class="text-primary">标题</span>
    <el-button type="primary">操作</el-button>
  </div>
</template>
```

## 文件结构

```
frontend/src/views/admin/
├── styles/
│   └── common.css          # Admin 通用样式规范
├── Layout.vue              # 管理后台布局（已导入 common.css）
├── Users.vue               # 用户管理页面
├── Datasources.vue         # 数据源管理页面
└── ...
```

## 维护说明

1. 所有新增的 Admin 页面会自动应用 `common.css` 中的样式
2. 修改 `common.css` 会影响所有 Admin 页面，请谨慎修改
3. 页面特定样式请在组件的 `<style scoped>` 中定义
4. 保持设计一致性优先于个性化需求

## 检查清单

新增/修改页面时请确认：
- [ ] 卡片圆角是否为 12px
- [ ] 表格字体是否为 13px
- [ ] 按钮是否有渐变效果
- [ ] 标签是否使用统一色值
- [ ] 间距是否符合 8px 网格系统
- [ ] 交互效果是否符合规范

---
文档版本：1.0
最后更新：2026-04-05
