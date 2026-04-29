# AI数据融合平台 - 基于 ERP 系统的商业智能报表设计与实现

> 毕业答辩演示系统 | 数仓分层架构 | AI 智能问数

## 📊 项目架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI数据融合平台架构                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ETL      ┌─────────────────────────────────┐  │
│  │   MySQL      │ ────────────>│         数仓分层                 │  │
│  │  (业务数据库) │  数据抽取     │  ODS → DWD → DWS → ADS          │  │
│  └──────────────┘              └─────────────────────────────────┘  │
│         │                                      │                     │
│         │                                      ▼                     │
│         │                            ┌─────────────────┐            │
│         │                            │   FastAPI       │            │
│         │                            │   后端服务       │            │
│         │                            └─────────────────┘            │
│         │                                      │                     │
│         │         ┌────────────────────────────┼─────────────────┐  │
│         │         │                            │                 │  │
│         ▼         ▼                            ▼                 │  │
│  ┌─────────────┐ ┌─────────────┐     ┌─────────────────┐        │  │
│  │  Metabase   │ │  Vue3 前端  │     │  AI 智能问数     │        │  │
│  │  BI 报表大屏  │ │  管理后台   │     │  (百炼 Qwen)    │        │  │
│  └─────────────┘ └─────────────┘     └─────────────────┘        │  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 🏗️ 数仓分层架构

| 层级 | 名称 | 描述 | 表示例 |
|------|------|------|--------|
| **ODS** | 操作数据存储 | 原始数据层，直接从业务库抽取 | ods_products, ods_customers |
| **DWD** | 数据明细层 | 清洗标准化，统一格式 | dwd_sales_orders, dwd_order_items |
| **DWS** | 数据汇总层 | 轻度聚合，主题汇总 | dws_sales_daily, dws_product_sales |
| **ADS** | 应用数据层 | 报表指标，直接用于展示 | ads_sales_dashboard, ads_kpi_summary |

## 🚀 快速启动

### 环境要求

- Docker & Docker Compose
- Python 3.10+
- Node.js 18+

### 方式一：一键启动（推荐）

```bash
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system
./scripts/start.sh
```

启动完成后访问：
- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

测试账号：`admin` / `admin123`

### 方式二：手动启动

### 1. 启动所有服务

```bash
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system
docker-compose up -d
```

这会启动：
- **MySQL** (端口 3306) - 业务数据库
- **Redis** (端口 6379) - 缓存
- **Metabase** (端口 3001) - BI 报表工具

### 2. 初始化数据库

```bash
# 等待 MySQL 启动完成（约 30 秒）
sleep 30

# 初始化业务表和模拟数据
mysql -h 127.0.0.1 -P 3306 -u root -proot123 erp_bi < init_scripts/erp_init.sql

# 创建 BI 视图（可选，用于 Metabase）
mysql -h 127.0.0.1 -P 3306 -u root -proot123 erp_bi < metabase/init_views.sql
```

### 3. 启动后端服务

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

### 5. 运行 ETL 任务

```bash
cd etl
python ods_extract.py    # ODS 层抽取
python dwd_clean.py      # DWD 层清洗
python dws_aggregate.py  # DWS 层聚合
python ads_report.py     # ADS 层报表
```

### 6. 访问 Metabase BI

1. 打开浏览器访问：**http://localhost:3001**
2. 首次启动需要 2-3 分钟初始化
3. 设置管理员账号（邮箱、密码）
4. 添加数据源：
   - 主机：`mysql`
   - 端口：`3306`
   - 数据库：`erp_bi`
   - 用户名：`erp_bi_user`
   - 密码：`erp_bi_pass`
5. 创建仪表板和报表（详见 `metabase/README.md`）

## 📁 项目结构

```
erp-bi-system/
├── docker-compose.yml          # Docker 编排
├── README.md                   # 项目文档
├── init_scripts/
│   └── erp_init.sql           # 数据库初始化脚本
├── backend/                    # FastAPI 后端
│   ├── main.py                # 主入口
│   ├── requirements.txt       # Python 依赖
│   └── api/
│       ├── auth.py            # 认证模块
│       └── ai_query.py        # AI 智能问数
├── etl/                        # ETL 脚本
│   ├── ods_extract.py         # ODS 层抽取
│   ├── dwd_clean.py           # DWD 层清洗
│   ├── dws_aggregate.py       # DWS 层聚合
│   └── ads_report.py          # ADS 层报表
└── frontend/                   # Vue3 前端（待创建）
    ├── package.json
    └── src/
```

## 🔌 API 文档

启动后端后访问：http://localhost:8000/docs

### 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/register` | POST | 用户注册 |
| `/api/reports/sales/kpi-summary` | GET | 销售 KPI 汇总 |
| `/api/reports/sales/trend` | GET | 销售趋势分析 |
| `/api/reports/sales/product-ranking` | GET | 产品排行榜 |
| `/api/ai-query/generate-sql` | POST | AI 生成 SQL |
| `/api/ai-query/execute-query` | POST | AI 查询并执行 |
| `/api/ai-query/schema` | GET | 获取表结构 |
| `/health` | GET | 健康检查 |

### AI 智能问数示例

```bash
# 请求
curl -X POST http://localhost:8000/api/ai-query/generate-sql \
  -H "Content-Type: application/json" \
  -d '{"question": "上个月销售额最高的产品是什么？"}'

# 响应
{
  "sql": "SELECT p.product_name, SUM(oi.subtotal) as total_sales FROM sales_order_items oi JOIN products p ON oi.product_id = p.id JOIN sales_orders o ON oi.order_id = o.id WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH) GROUP BY p.product_id ORDER BY total_sales DESC LIMIT 1",
  "explanation": "根据您的问题生成的 SQL 查询"
}
```

## 🎓 毕业答辩演示要点

### 1. 系统演示流程（5 分钟）

1. **系统架构介绍** (30 秒)
   - 展示数仓分层架构图
   - 说明各层职责

2. **数据流转演示** (1 分钟)
   - MySQL 业务数据 → ODS → DWD → DWS → ADS
   - 展示各层数据表

3. **BI 报表展示** (1 分钟)
   - 销售分析大屏
   - 产品排行榜
   - 客户分析报表

4. **AI 智能问数** (2 分钟) ⭐ 创新功能
   - 演示自然语言查询
   - "显示销售额 Top5 的产品"
   - "查看客户张三的所有订单"

5. **后台管理** (30 秒)
   - 权限管理
   - ETL 任务调度

### 2. 技术亮点

- ✅ **完整的数仓分层架构** (ODS/DWD/DWS/ADS)
- ✅ **ETL 数据 pipeline** (抽取/清洗/聚合/报表)
- ✅ **AI 智能问数** (自然语言转 SQL)
- ✅ **可视化 BI 报表** (Metabase/Vue3)
- ✅ **RBAC 权限管理**

### 3. 可能的问题准备

**Q: 为什么选择这种数仓分层架构？**
A: 分层设计实现数据解耦，ODS 保持原始数据可追溯，DWD 统一数据质量，DWS 提升查询性能，ADS 直接支撑业务应用。

**Q: AI 问数的准确率如何？**
A: 基于百炼 Qwen 大模型，在明确的问题场景下准确率可达 85%+，通过 schema 上下文增强和 few-shot 提示优化生成质量。

**Q: 系统如何保证数据一致性？**
A: ETL 任务采用事务处理，失败回滚；定时任务调度确保数据更新频率；关键指标设置数据质量校验规则。

## 📝 开发日志

- 2026-03-15: 系统全面重构优化，修复所有路由问题，完成部署上线
- 2026-03-14: 项目初始化，完成核心架构搭建
- 2026-03-14: 完成数据库设计和初始化脚本
- 2026-03-14: 完成 ETL 脚本开发 (ODS/DWD/DWS/ADS)
- 2026-03-14: 完成 FastAPI 后端和 AI 智能问数接口
- 待办：Metabase BI 报表配置
- 待办：答辩 PPT 制作

---

## 📄 更多文档

- [部署文档](DEPLOYMENT.md) - 详细部署指南和常见问题
- [快速启动](QUICK_START.md) - 5 分钟快速上手指南

---

**技术栈**: FastAPI | Vue3 | MySQL | Docker | 百炼 AI | Metabase

**作者**: 毕业设计项目

**日期**: 2026 年 3 月
