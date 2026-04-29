# AI 问数功能使用说明

## 概述

AI 问数功能支持将自然语言转换为 SQL 查询，并提供以下增强功能：
- ✅ 关键词提取与标准 SQL 匹配（节省 token）
- ✅ 详细的问数日志记录
- ✅ Token 消耗统计
- ✅ 执行时间监控
- ✅ 标准 SQL 库管理

## 配置

### 1. 配置百炼 API Key

在 `backend/.env` 文件中配置：

```bash
# 从 https://dashscope.console.aliyun.com/apiKey 获取
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
DASHSCOPE_MODEL=qwen-plus
```

### 2. 启动后端服务

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API 接口

### 1. AI 生成 SQL

**POST** `/api/ai-query/generate-sql`

```bash
curl -X POST http://localhost:8000/api/ai-query/generate-sql \
  -H "Content-Type: application/json" \
  -d '{
    "question": "上个月销售额最高的产品是什么？",
    "top_k": 10
  }'
```

**响应：**
```json
{
  "sql": "SELECT ...",
  "explanation": "根据您的问题生成的 SQL 查询",
  "data": null,
  "columns": null,
  "tokens_used": 150,
  "execution_time_ms": 234,
  "matched_standard": false,
  "log_id": 1
}
```

### 2. AI 执行查询

**POST** `/api/ai-query/execute-query`

```bash
curl -X POST http://localhost:8000/api/ai-query/execute-query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "上个月销售额最高的产品是什么？",
    "top_k": 10
  }'
```

**响应：**
```json
{
  "sql": "SELECT ...",
  "explanation": "根据您的问题生成的 SQL 查询",
  "data": [...],
  "columns": ["product_name", "total_sales"],
  "tokens_used": 150,
  "execution_time_ms": 345,
  "matched_standard": false,
  "log_id": 2
}
```

### 3. 提取关键词

**POST** `/api/ai-query/extract-keywords`

```bash
curl -X POST http://localhost:8000/api/ai-query/extract-keywords \
  -H "Content-Type: application/json" \
  -d '{
    "question": "上个月销售额最高的产品是什么？"
  }'
```

**响应：**
```json
{
  "keywords": ["产品", "销售", "上月", "排行"]
}
```

### 4. 标准 SQL 库管理

#### 获取标准 SQL 列表

**GET** `/api/ai-query/standard-sql`

```bash
curl http://localhost:8000/api/ai-query/standard-sql
```

#### 创建标准 SQL

**POST** `/api/ai-query/standard-sql`

```bash
curl -X POST http://localhost:8000/api/ai-query/standard-sql \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["产品", "排行", "销售额"],
    "question_template": "销售额最高的产品是什么？",
    "standard_sql": "SELECT p.product_name, SUM(oi.subtotal) as total_sales FROM products p JOIN sales_order_items oi ON p.id = oi.product_id GROUP BY p.id ORDER BY total_sales DESC LIMIT 1",
    "explanation": "查询销售额最高的产品"
  }'
```

#### 更新标准 SQL

**PUT** `/api/ai-query/standard-sql/{sql_id}`

```bash
curl -X PUT http://localhost:8000/api/ai-query/standard-sql/1 \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": 0
  }'
```

#### 删除标准 SQL

**DELETE** `/api/ai-query/standard-sql/{sql_id}`

```bash
curl -X DELETE http://localhost:8000/api/ai-query/standard-sql/1
```

### 5. 问数日志查询

#### 获取日志列表

**GET** `/api/ai-query/logs`

```bash
# 获取最近 20 条日志
curl http://localhost:8000/api/ai-query/logs

# 分页查询
curl http://localhost:8000/api/ai-query/logs?limit=10&offset=0

# 按状态筛选
curl http://localhost:8000/api/ai-query/logs?status=success
curl http://localhost:8000/api/ai-query/logs?status=failed
```

**响应：**
```json
{
  "total": 100,
  "limit": 20,
  "offset": 0,
  "data": [
    {
      "id": 1,
      "question": "上个月销售额最高的产品是什么？",
      "generated_sql": "SELECT ...",
      "keywords": ["产品", "销售", "上月", "排行"],
      "input_tokens": 100,
      "output_tokens": 50,
      "total_tokens": 150,
      "execution_time_ms": 234,
      "status": "success",
      "error_message": null,
      "created_at": "2026-03-17 08:57:00"
    }
  ]
}
```

#### 获取统计信息

**GET** `/api/ai-query/logs/stats`

```bash
curl http://localhost:8000/api/ai-query/logs/stats
```

**响应：**
```json
{
  "total_queries": 100,
  "success_count": 95,
  "failed_count": 5,
  "avg_execution_time_ms": 245.67,
  "total_tokens_consumed": 15000,
  "matched_standard_count": 30
}
```

## 工作流程

### AI 问数流程

```
用户问题
    ↓
提取关键词
    ↓
匹配标准 SQL 库 ────→ 匹配成功 ────→ 使用标准 SQL (tokens=0)
    ↓                                    ↓
匹配失败                            记录日志
    ↓                                    ↓
调用百炼 AI 生成 SQL                     返回结果
    ↓
记录日志
    ↓
返回结果
```

### 标准 SQL 积累流程

1. AI 生成成功的 SQL 查询
2. 管理员在后台查看问数日志
3. 筛选高频、通用的查询
4. 通过 API 添加到标准 SQL 库
5. 后续相同类型问题直接匹配标准 SQL

## 示例问题

系统支持以下类型的自然语言查询：

### 产品相关
- "销售额最高的产品是什么？"
- "各品类的销售占比是多少？"
- "库存数量最多的产品有哪些？"

### 客户相关
- "客户张三的订单有哪些？"
- "企业客户有多少个？"
- "各行业的客户分布如何？"

### 销售相关
- "上个月的销售额是多少？"
- "本月销售趋势如何？"
- "季度销售排行榜"

### 时间相关
- 今天、昨天、本周、上周、本月、上月、今年、去年

## 日志监控

建议定期检查问数日志：

1. **失败查询分析** - 查看 `status=failed` 的日志，优化 AI 提示词
2. **Token 消耗监控** - 查看 `total_tokens`，控制成本
3. **标准 SQL 优化** - 将高频查询纳入标准库
4. **性能分析** - 查看 `execution_time_ms`，优化查询性能

## 故障排查

### 问题：AI 问数返回 "AI 服务未配置"

**原因：** DASHSCOPE_API_KEY 未配置或为默认值

**解决：**
1. 访问 https://dashscope.console.aliyun.com/apiKey 获取 API Key
2. 在 `backend/.env` 文件中配置 `DASHSCOPE_API_KEY=sk-xxxxx`
3. 重启后端服务

### 问题：SQL 执行失败

**原因：** 生成的 SQL 语法错误或表名/字段名不正确

**解决：**
1. 查看问数日志中的 `generated_sql` 和 `error_message`
2. 在数据库客户端手动执行 SQL 验证
3. 如确认为 AI 生成错误，可添加到标准 SQL 库

### 问题：关键词匹配不准确

**解决：**
1. 查看 `api/ai_query.py` 中的 `extract_keywords` 函数
2. 在 `keyword_patterns` 字典中添加新的关键词映射
3. 优化标准 SQL 库的关键词设置

## 最佳实践

1. **优先使用标准 SQL** - 对于常见查询，先添加到标准库
2. **定期清理日志** - 避免日志表过大，可定期归档旧日志
3. **监控 Token 消耗** - 设置预算告警，控制 AI 调用成本
4. **优化关键词词典** - 根据实际使用情况持续优化
5. **人工审核标准 SQL** - 确保标准 SQL 的正确性和安全性
