# AI数据融合平台快速启动指南

## 5 分钟快速启动

### 第一步：检查环境

```bash
# 检查 Docker
docker --version

# 检查 Python
python3 --version

# 检查 Node.js
node --version
```

### 第二步：启动服务

```bash
# 进入项目目录
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system

# 一键启动
./scripts/start.sh
```

### 第三步：访问系统

打开浏览器访问：http://localhost:3000

使用测试账号登录：
- 用户名：`admin`
- 密码：`admin123`

## 主要功能

### 1. 仪表板 Dashboard

访问路径：`/dashboard`

功能：
- 销售 KPI 指标展示
- 销售趋势图表
- 产品排行榜
- 品类分布图

### 2. 销售报表

访问路径：`/reports/sales`

功能：
- 销售 KPI 汇总
- 销售趋势分析
- 产品销售排行榜
- 品类分析

### 3. 数据预览

访问路径：`/data`

功能：
- 查看各数据库表数据
- 支持分页和筛选

### 4. ETL 任务

访问路径：`/etl`

功能：
- 查看 ETL 任务列表
- 手动执行 ETL 任务
- 查看任务日志

### 5. AI 智能问数

访问路径：`/ai-query`

功能：
- 自然语言生成 SQL
- 执行查询并返回结果
- 查看数据库表结构

示例问题：
- "上个月销售额最高的产品是什么？"
- "客户张三的订单有哪些？"
- "各品类的销售占比是多少？"

## API 接口

### 查看 API 文档

访问：http://localhost:8000/docs

### 常用 API

```bash
# 健康检查
curl http://localhost:8000/health

# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取 KPI 汇总 (需要 token)
curl http://localhost:8000/api/reports/sales/kpi-summary \
  -H "Authorization: Bearer <your-token>"

# 获取销售趋势
curl "http://localhost:8000/api/reports/sales/trend?months=12" \
  -H "Authorization: Bearer <your-token>"

# AI 生成 SQL
curl -X POST http://localhost:8000/ai-query/generate-sql \
  -H "Content-Type: application/json" \
  -d '{"question":"销售额最高的产品"}'
```

## 停止服务

```bash
./scripts/stop.sh
```

## 重启服务

```bash
# 停止
./scripts/stop.sh

# 启动
./scripts/start.sh
```

## 数据库访问

```bash
# 命令行访问 MySQL
docker exec -it erp-bi-mysql mysql -uroot -proot123

# 使用 Metabase (图形化)
# 访问 http://localhost:3001
```

## 主要数据库表

```sql
-- 产品表
SELECT * FROM erp_source.products LIMIT 10;

-- 客户表
SELECT * FROM erp_source.customers LIMIT 10;

-- 销售订单
SELECT * FROM erp_source.sales_orders ORDER BY created_at DESC LIMIT 10;

-- 库存表
SELECT * FROM erp_source.inventory LIMIT 10;
```

## 数据分层

| 数据库 | 说明 |
|--------|------|
| erp_source | 源数据库，ERP 业务表 |
| erp_ods | 操作数据存储层 |
| erp_dwd | 明细数据层 |
| erp_dws | 汇总数据层 |
| erp_ads | 应用数据层 |

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + ECharts |
| 后端 | FastAPI (Python) |
| 数据库 | MySQL 8.0 |
| 缓存 | Redis 7 |
| BI | Metabase |
| 容器 | Docker + Docker Compose |

## 需要帮助？

查看完整文档：[DEPLOYMENT.md](./DEPLOYMENT.md)
