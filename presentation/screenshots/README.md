# 系统截图采集说明

## 截图采集方法

由于需要浏览器环境进行截图，请按照以下步骤手动采集截图：

### 方法一：使用浏览器自带截图（推荐）

1. 打开 Chrome/Edge 浏览器
2. 访问对应页面
3. 按 `F12` 打开开发者工具
4. 按 `Cmd+Shift+P` (Mac) 或 `Ctrl+Shift+P` (Windows)
5. 输入 "screenshot" 选择 "Capture full size screenshot"

### 方法二：使用系统截图工具

- **Mac**: `Cmd+Shift+4` 选择区域截图
- **Windows**: `Win+Shift+S` 截图
- **Linux**: `PrintScreen` 或 `gnome-screenshot`

### 方法三：使用 Playwright（自动化）

```bash
npm install -g playwright
npx playwright screenshot http://localhost:3000/login screenshots/login.png
```

---

## 需要采集的截图

### 1. 登录页面
- **URL**: http://localhost:3000/login
- **保存为**: `login.png`
- **要求**: 展示登录表单和系统标题

### 2. 仪表板
- **URL**: http://localhost:3000/dashboard
- **保存为**: `dashboard.png`
- **要求**: 展示 KPI 卡片和主要图表

### 3. AI 问数页面
- **URL**: http://localhost:3000/ai-query
- **保存为**: `ai-query.png`
- **要求**: 展示输入框和查询结果

### 4. 销售报表
- **URL**: http://localhost:3000/reports/sales
- **保存为**: `reports.png`
- **要求**: 展示销售数据表格和图表

### 5. Metabase 仪表板
- **URL**: http://localhost:3001
- **保存为**: `metabase.png`
- **要求**: 展示 Metabase 主界面或仪表板

---

## 截图占位符

当前 PPT 使用占位符显示，采集截图后：

1. 将截图保存到 `presentation/screenshots/` 目录
2. 确保文件名与 PPT 中引用一致
3. 重新导出 PPT 即可显示图片

---

## 快速截图脚本

```bash
#!/bin/bash
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system/presentation/screenshots

# 使用 playwright 截图
npx playwright screenshot http://localhost:3000/login login.png --full-page
npx playwright screenshot http://localhost:3000/dashboard dashboard.png --full-page
npx playwright screenshot http://localhost:3000/ai-query ai-query.png --full-page
npx playwright screenshot http://localhost:3000/reports/sales reports.png --full-page
npx playwright screenshot http://localhost:3001 metabase.png --full-page

echo "截图完成！"
```

---

## 截图清单（完成后勾选）

- [ ] login.png - 登录页面
- [ ] dashboard.png - 仪表板
- [ ] ai-query.png - AI 问数
- [ ] reports.png - 销售报表
- [ ] metabase.png - Metabase BI

**当前状态**: 等待截图采集
