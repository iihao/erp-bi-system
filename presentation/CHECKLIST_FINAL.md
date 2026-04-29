# AI数据融合平台毕业答辩 - 材料清单

> 本文档整理了答辩所需的全部材料、检查项和打包建议，确保答辩准备完整无遗漏。

---

## 一、答辩材料清单

### 核心材料

| # | 材料 | 文件路径 | 状态 | 说明 |
|---|------|----------|------|------|
| 1 | PPT 演示文稿 | `presentation/ERP-BI 答辩.pptx` | ✅ | 23 页，2.9MB |
| 2 | PPT 源代码 | `presentation/ERP-BI 答辩.md` | ✅ | Marp 格式，可重新编译 |
| 3 | 系统架构图 | `presentation/architecture.svg` | ✅ | Mermaid 生成 |
| 4 | 架构图源码 | `presentation/architecture.mmd` | ✅ | 可修改重绘 |
| 5 | 页面截图 | `presentation/screenshots/*.png` | ✅ | 5 张实际截图 |
| 6 | 截图占位图 | `presentation/screenshots/*.svg` | ✅ | 5 张 SVG 占位图 |

### 准备材料

| # | 材料 | 文件路径 | 状态 | 说明 |
|---|------|----------|------|------|
| 7 | README 使用说明 | `presentation/README.md` | ✅ v2.0 | 文件清单和使用说明 |
| 8 | 演讲备注 | `presentation/speaker_notes.md` | ✅ v2.0 | 21 页逐页讲解词 |
| 9 | 演示检查清单 | `presentation/demo_checklist.md` | ✅ v1.0 | 环境/账号/数据检查 |
| 10 | Live Demo 指南 | `presentation/DEMO_SCRIPT_GUIDE.md` | ✅ v2.0 | 逐秒操作指南 ⭐ |
| 11 | Q&A 问答准备 | `presentation/QA_PREPARATION.md` | ✅ v1.0 | 22 题参考答案 ⭐ |

### 论文材料

| # | 材料 | 文件路径 | 状态 | 说明 |
|---|------|----------|------|------|
| 12 | 论文 PDF | `docs/thesis.pdf` | ✅ | 完整论文 |
| 13 | 论文文本 | `docs/thesis.txt` | ✅ | UTF-8 文本版 |
| 14 | 章节重构稿 | `docs/第4-7章_*.txt` | ✅ | 各章重构稿 |

---

## 二、演示环境准备

### 服务清单

| 服务 | 端口 | 启动命令 | 检查方式 |
|------|------|----------|----------|
| MySQL | 3306 | `docker-compose up -d mysql` | `docker-compose ps` |
| Redis | 6379 | `docker-compose up -d redis` | `docker-compose ps` |
| FastAPI | 8000 | `docker-compose up -d fastapi` | `curl http://localhost:8000/health` |
| 前端 | 3000 | `docker-compose up -d frontend` | `curl http://localhost:3000/login` |
| Metabase | 3001 | `docker-compose up -d metabase` | `curl http://localhost:3001` |

### 一键启动

```bash
cd /Users/huangqiang/projects/erp-bi-system
docker-compose up -d
```

### 测试账号

| 账号 | 密码 | 用途 |
|------|------|------|
| admin | admin123 | 系统登录 |

---

## 三、数据准备

### ETL 执行

```bash
# 执行 ETL 流程（确保 ADS 层有数据）
cd /Users/huangqiang/projects/erp-bi-system
# 通过系统界面执行 ETL，或通过 API 触发
```

### 数据检查

| 层级 | 预期数据量 | 检查方式 |
|------|-----------|----------|
| ODS | > 5000 条 | 查询 `ods_orders` 等表行数 |
| DWD | > 4800 条 | 查询 `dwd_orders` 等表行数 |
| DWS | > 300 条 | 查询 `dws_sales_daily` 行数 |
| ADS | > 50 条 | 查询 `ads_kpi_summary` 行数 |

---

## 四、答辩流程

### 答辩前（提前 30 分钟）

- [ ] 到达答辩教室
- [ ] 连接投影仪/共享屏幕
- [ ] 打开 PPT 文件
- [ ] 全屏预览一遍，确认格式正常
- [ ] 打开备用截图文件夹
- [ ] 手机静音，保持专注

### 汇报阶段（5 分钟）

| 时间 | 内容 | PPT 页码 | 备注 |
|------|------|----------|------|
| 0:00-0:15 | 封面 | 第 1 页 | 自我介绍 |
| 0:15-0:30 | 目录 | 第 2 页 | 概述 |
| 0:30-1:00 | 项目背景 | 第 3 页 | |
| 1:00-1:30 | 项目目标 | 第 4 页 | |
| 1:30-2:00 | 系统架构 | 第 5-6 页 | 架构图 |
| 2:00-2:30 | 数仓分层 | 第 7-8 页 | 4 层 24 表 |
| 2:30-3:00 | ETL 流程 | 第 9-10 页 | |
| 3:00-3:20 | 技术栈 | 第 11 页 | |
| 3:20-4:00 | 核心功能 | 第 12-13 页 | 仪表板 + 图表 |
| 4:00-4:40 | AI 智能问数 | 第 14-15 页 | 重点 ⭐ |
| 4:40-5:00 | Metabase + 总结 | 第 16-20 页 | |

### Q&A 阶段（5-10 分钟）

- [ ] 记录评委问题
- [ ] 参考 `QA_PREPARATION.md` 作答
- [ ] 遇到不会的问题坦诚承认

---

## 五、备份方案

### 备份材料

| 方案 | 内容 | 适用场景 |
|------|------|----------|
| PPT 截图 | 嵌入 PPT 中的系统截图 | 演示环境部分异常 |
| 截图文件夹 | `screenshots/` 下全部 PNG | 演示环境完全不可用 |
| PDF 论文 | `docs/thesis.pdf` | 评委要求看论文细节 |

### 紧急联系人

| 角色 | 联系方式 |
|------|----------|
| 技术支持 | [填写] |
| 指导老师 | [填写] |

---

## 六、文件打包建议

### 答辩材料打包

将所有材料打包为一个 zip 文件，方便携带和备份：

```bash
cd /Users/huangqiang/projects/erp-bi-system
zip -r 答辩材料.zip \
  presentation/ERP-BI\ 答辩.pptx \
  presentation/ERP-BI\ 答辩.md \
  presentation/architecture.svg \
  presentation/architecture.mmd \
  presentation/speaker_notes.md \
  presentation/demo_checklist.md \
  presentation/DEMO_SCRIPT_GUIDE.md \
  presentation/QA_PREPARATION.md \
  presentation/README.md \
  presentation/screenshots/ \
  docs/thesis.pdf \
  docs/thesis.txt
```

---

## 七、检查清单（答辩前一天）

### 材料检查

- [ ] PPT 文件存在且格式正常
- [ ] 截图清晰，关键功能有截图
- [ ] 演讲备注已熟悉
- [ ] Q&A 准备已阅读
- [ ] 论文 PDF 已准备好

### 环境检查

- [ ] Docker 服务正常启动
- [ ] 前端可访问
- [ ] 后端 API 正常
- [ ] 数据库有数据
- [ ] Metabase 可访问
- [ ] AI 问数可调用

### 演练检查

- [ ] 完整演练 3 遍以上
- [ ] 每遍计时，控制在 5 分钟内
- [ ] 模拟异常情况，练习切换备用方案
- [ ] 对每个 PPT 页面，能流畅说出讲解词

---

**最后更新：** 2026 年 4 月 28 日
**版本：** v1.0
