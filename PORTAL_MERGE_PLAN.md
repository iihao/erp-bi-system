# 前台门户融合方案

## 路由结构

```
/portal          → 仪表板（原 dashboard 内容）
/portal/reports  → 报表列表
/portal/ai-query → AI 智能问数
/portal/login    → 登录页
```

## 布局风格

**商务稳重风格：**
- 左侧深色侧边栏（#1e293b → #0f172a 渐变）
- 顶部简洁 Header
- 主内容区浅灰背景（#f5f7fa）
- 卡片式布局，圆角 8px
- 主色调：深蓝（#2c5282）

## 修改内容

1. **router/index.js** - 删除 /dashboard 路由，统一使用 /portal
2. **portal/Layout.vue** - 优化样式，统一商务风格
3. **portal/Dashboard.vue** - 整合原 dashboard 内容
4. **删除** - MainLayout.vue（不再使用）
