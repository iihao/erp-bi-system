# 可视化报表模块 - 开发文档

## 📊 模块概述

可视化报表模块是 AI数据融合平台的核心功能之一，提供丰富的销售数据可视化展示，包括销售趋势分析、产品排行榜、品类分析和客户分析等多个维度。

## 🏗️ 技术架构

### 前端技术栈
- **Vue 3** - 渐进式 JavaScript 框架
- **Element Plus** - UI 组件库
- **ECharts 5** - 数据可视化图表库
- **Axios** - HTTP 客户端
- **Vue Router** - 路由管理

### 后端技术栈
- **FastAPI** - 高性能 Python Web 框架
- **Pydantic** - 数据验证和序列化
- **JWT** - 身份认证

## 📁 文件结构

```
erp-bi-system/
├── backend/
│   ├── api/
│   │   └── reports.py          # 报表 API 端点
│   └── main.py                  # 主入口（已注册 reports 路由）
└── frontend/
    ├── src/
    │   ├── views/
    │   │   └── reports/
    │   │       └── SalesReport.vue    # 销售报表页面
    │   ├── components/
    │   │   └── NavBar.vue             # 导航栏（已添加报表入口）
    │   └── router/
    │       └── index.js               # 路由配置（已添加 /reports/sales）
    └── package.json                   # 已添加 echarts 依赖
```

## 🔌 API 端点

所有报表 API 都需要 Bearer Token 认证。

### 1. 获取 KPI 汇总指标
```http
GET /api/reports/sales/kpi-summary
Authorization: Bearer {token}
```

**响应示例：**
```json
[
  {"kpi_name": "总销售额", "kpi_value": 5234567.89, "unit": "元"},
  {"kpi_name": "总订单数", "kpi_value": 23456, "unit": "单"},
  {"kpi_name": "总销售量", "kpi_value": 89012, "unit": "件"}
]
```

### 2. 获取销售趋势数据
```http
GET /api/reports/sales/trend?months=12
Authorization: Bearer {token}
```

**参数：**
- `months`: 查询月数（1-24，默认 12）

**响应示例：**
```json
[
  {
    "month": "2026-01",
    "sales_amount": 1234567.89,
    "order_count": 2345,
    "quantity": 8901
  }
]
```

### 3. 获取产品排行榜
```http
GET /api/reports/sales/product-ranking?limit=10
Authorization: Bearer {token}
```

**参数：**
- `limit`: 返回数量（1-50，默认 10）

### 4. 获取品类分析数据
```http
GET /api/reports/sales/category-analysis
Authorization: Bearer {token}
```

### 5. 获取客户分析数据
```http
GET /api/reports/customer/analysis
Authorization: Bearer {token}
```

### 6. 获取仪表板概览
```http
GET /api/reports/dashboard/overview
Authorization: Bearer {token}
```

## 📈 图表展示

### 1. KPI 卡片
- 总销售额
- 总订单数
- 总销售量
- 产品种类数
- 客户总数
- 平均客单价

### 2. 销售趋势图（折线图 + 柱状图）
- 双 Y 轴设计
- 折线：销售额（带面积渐变）
- 柱状：订单数
- 支持 6/12/24 月切换

### 3. 品类销售分布（环形饼图）
- 展示各品类销售占比
- 交互式图例
- 中心显示总计

### 4. 产品销量排行榜（条形图）
- Top 5/10/20 可切换
- 渐变色条形
- 数值标签显示

### 5. 客户类型分析（饼图）
- 按客户类型聚合
- 百分比显示
- 交互式提示

## 🎨 页面功能

### 主要功能
1. **数据刷新** - 手动刷新所有图表数据
2. **时间范围切换** - 销售趋势支持 6/12/24 月
3. **排行榜数量切换** - 支持 Top 5/10/20
4. **响应式布局** - 自适应不同屏幕尺寸
5. **图表自适应** - 窗口大小变化时自动调整

### 交互特性
- 卡片悬停效果
- 图表工具提示
- 图例点击筛选
- 数据加载状态
- 错误提示消息

## 🚀 快速启动

### 1. 启动后端服务
```bash
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端服务
```bash
cd /Users/huangqiang/.openclaw/workspace/erp-bi-system/frontend
npm run dev
```

### 3. 访问报表页面
打开浏览器访问：**http://localhost:3000/reports/sales**

## 🔐 认证说明

所有报表 API 都需要 JWT Token 认证：

1. 先通过 `/api/auth/login` 获取 token
2. 在请求头中添加：`Authorization: Bearer {token}`
3. Token 有效期默认为 24 小时

**登录示例：**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## 📊 模拟数据

当前版本使用模拟数据用于演示，数据结构参考了 `etl/ads_report.py` 中的 ADS 层报表指标。

**后续优化方向：**
1. 连接真实数据库（MySQL）
2. 从 ADS 层读取实际报表数据
3. 添加数据缓存机制
4. 支持实时数据更新

## 🎯 参考 Metabase 功能

本模块参考了 Metabase 的核心报表功能：

| Metabase 功能 | 本系统实现 |
|--------------|-----------|
| 仪表板 | KPI 卡片 + 图表组合 |
| 问题（Question） | 预定义报表端点 |
| 可视化 | ECharts 图表库 |
| 筛选器 | 时间范围/数量选择器 |
| 下钻 | 待实现 |

## 🔮 后续开发计划

### 短期（v1.1）
- [ ] 连接真实数据库
- [ ] 添加数据导出功能（Excel/CSV）
- [ ] 实现报表订阅和定时推送
- [ ] 添加更多图表类型（地图、漏斗图等）

### 中期（v1.2）
- [ ] 自定义仪表板（拖拽布局）
- [ ] 报表权限管理
- [ ] 数据下钻和联动
- [ ] 移动端适配优化

### 长期（v2.0）
- [ ] 自助式报表构建器
- [ ] AI 智能报表推荐
- [ ] 实时数据流处理
- [ ] 多数据源支持

## 📝 开发日志

- **2026-03-14**: 完成报表模块基础开发
  - ✅ 创建后端 API 端点（6 个）
  - ✅ 创建 SalesReport.vue 组件
  - ✅ 集成 ECharts 图表库
  - ✅ 配置路由和导航
  - ✅ 实现 5 种图表类型
  - ✅ 添加响应式布局

---

**开发者**: AI数据融合 项目团队  
**版本**: v1.0.0  
**更新日期**: 2026 年 3 月 14 日
