# AI数据融合 毕业答辩 PPT - 使用说明

## 📁 文件清单

### 主要文件
```
presentation/
├── ERP-BI 答辩.pptx          # PowerPoint 演示文稿（2.9MB）
├── ERP-BI 答辩.md            # Marp 源代码（可重新编译）
├── architecture.svg          # 系统架构图
├── architecture.mmd          # Mermaid 源码
├── speaker_notes.md          # 演讲备注（完整版）
├── demo_checklist.md         # 演示检查清单（v1.0）
├── DEMO_SCRIPT_GUIDE.md      # Live Demo 详细操作指南（v2.0）⭐ 新增
├── QA_PREPARATION.md         # 评委 Q&A 问答准备 ⭐ 新增
└── screenshots/
    ├── README.md             # 截图采集说明
    ├── login.svg             # 登录页占位图
    ├── login.png             # 登录页截图
    ├── dashboard.svg         # 仪表板占位图
    ├── dashboard.png         # 仪表板截图
    ├── ai-query.svg          # AI 问数占位图
    ├── ai-query.png          # AI 问数截图
    ├── reports.svg           # 报表页占位图
    ├── reports.png           # 报表页截图
    ├── metabase.svg          # Metabase 占位图
    └── metabase.png          # Metabase 截图
```

## 📊 PPT 结构（共 23 页）

| 页码 | 标题 | 预计时间 | 备注 |
|------|------|----------|------|
| 1 | 封面 | 15 秒 | |
| 2 | 目录 | 15 秒 | |
| 3 | 项目背景 | 30 秒 | |
| 4 | 项目目标 | 30 秒 | |
| 5 | 系统架构设计 | 30 秒 | 架构图 |
| 6 | 系统架构 - 分层说明 | 25 秒 | |
| 7 | 数仓分层设计 | 30 秒 | 4 层 24 表 |
| 8 | 数仓分层 - 详细设计 | 30 秒 | |
| 9 | ETL 流程实现 | 30 秒 | |
| 10 | ETL 执行演示 | 20 秒 | ⭐ 新增 |
| 11 | 技术栈介绍 | 20 秒 | |
| 12 | 核心功能 - 仪表板 | 30 秒 | |
| 13 | 核心功能 - 图表展示 | 20 秒 | |
| 14 | AI 智能问数 | 40 秒 | 核心创新点 |
| 15 | AI 智能问数 - 演示 | 30 秒 | 典型查询示例表 |
| 16 | Metabase BI 集成 | 20 秒 | |
| 17 | 系统测试结果 | 25 秒 | |
| 18 | 部署与运维 | 20 秒 | ⭐ 新增 |
| 19 | 创新点总结 | 30 秒 | |
| 20 | 总结与展望 | 25 秒 | |
| 21 | 致谢 | 10 秒 | |
| 22 | 附录：演示准备 | - | |
| 23 | Backup 技术细节 | - | |

**总时长：约 5 分钟**

## 🔄 更新截图（可选）

当前 PPT 使用 SVG 占位图。如需使用实际系统截图，请执行以下步骤：

### 方法 1：使用 Playwright 自动截图

```bash
# 1. 确保系统服务已启动
docker-compose ps

# 2. 安装 playwright 浏览器
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system/presentation
npx playwright install chromium

# 3. 自动截图
npx playwright screenshot http://localhost:3000/login screenshots/login.png --full-page
npx playwright screenshot http://localhost:3000/dashboard screenshots/dashboard.png --full-page
npx playwright screenshot http://localhost:3000/ai-query screenshots/ai-query.png --full-page
npx playwright screenshot http://localhost:3000/reports/sales screenshots/reports.png --full-page
npx playwright screenshot http://localhost:3001 screenshots/metabase.png --full-page

# 4. 重新生成 PPT
marp ERP-BI\ 答辩.md --output ERP-BI\ 答辩.pptx --allow-local-files
```

### 方法 2：手动截图

1. 使用浏览器访问各页面
2. 使用系统截图工具（Mac: Cmd+Shift+4）
3. 保存到 `screenshots/` 目录，替换 SVG 文件

## 🎤 演讲准备

### 1. 阅读演讲备注
详细演讲备注请参阅 `speaker_notes.md`，每页 PPT 都有对应的讲解词。

### 2. 检查演示环境
```bash
# 检查服务状态
docker-compose ps

# 检查前端
curl http://localhost:3000

# 检查 Metabase
curl http://localhost:3001
```

### 3. 准备测试数据
确保 ADS 层有足够的报表数据用于演示。

## 📝 演示检查清单

请参阅以下文档完成演示准备：

- [ ] 环境检查（Docker、前端、后端、数据库）— `demo_checklist.md`
- [ ] 账号准备（admin/admin123）— `demo_checklist.md`
- [ ] 数据准备（ODS、DWD、DWS、ADS 数据完整）— `demo_checklist.md`
- [ ] Live Demo 流程演练（3 遍以上）— `DEMO_SCRIPT_GUIDE.md`
- [ ] 评委 Q&A 问答准备 — `QA_PREPARATION.md`
- [ ] 截图采集（或使用占位图）— `screenshots/README.md`
- [ ] 演讲备注熟悉 — `speaker_notes.md`

## 🎯 验收标准

| 项目 | 状态 | 说明 |
|------|------|------|
| PPT 文件 | ✅ | ERP-BI 答辩.pptx (2.9MB, 23 页) |
| 架构图 | ✅ | architecture.svg |
| 截图 | ✅ | PNG 实际截图 + SVG 占位图 |
| 演讲备注 | ✅ | speaker_notes.md (5 分钟) |
| 演示指南 | ✅ | DEMO_SCRIPT_GUIDE.md (逐秒操作) |
| Q&A 准备 | ✅ | QA_PREPARATION.md (22 题) |
| 检查清单 | ✅ | demo_checklist.md |

## 📞 技术支持

如有问题，请检查：
1. Docker 服务是否正常启动
2. 端口 3000、3001、8000 是否被占用
3. 数据库连接是否正常

---

**最后更新：** 2026 年 4 月 28 日
**版本：** v2.0
