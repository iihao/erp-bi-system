# AI 问数 - 向量语义匹配层设计方案

## 目标

在标准 SQL 库关键词匹配和 AI LLM 调用之间，插入一层**向量语义匹配**，利用语义相似度复用已有查询结果，减少 LLM 调用。

## 当前三层架构

```
用户提问 → LRU Cache → 关键词匹配(score≥2) → ❌ → AI LLM
```

## 新四层架构

```
用户提问 → LRU Cache → 关键词匹配(score≥2) → 向量匹配(cos≥0.78) → ❌ → AI LLM
                                              ↓
                                       命中 → 直接返回 SQL
                                       (~100ms, 0 tokens)
```

## 技术选型

### 方案 A：纯 MySQL 向量计算（推荐）

不需要引入外部向量数据库，直接在 MySQL 中实现：

```sql
-- 新增表：存储历史查询的向量
CREATE TABLE query_vectors (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    query_text TEXT NOT NULL COMMENT '原始查询文本',
    query_vector JSON NOT NULL COMMENT '嵌入向量 (1024维)',
    sql_result TEXT NOT NULL COMMENT '对应的 SQL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created (created_at)
);
```

**优点**：
- 零依赖，不引入 Milvus/pgvector 等外部服务
- 数据量小（预计 < 10000 条），MySQL 完全胜任
- 向量计算在应用层完成，不加重 DB 负担

### 方案 B：DashScope Embedding API

使用阿里云百炼的 `text-embedding-v4` 模型，与当前 LLM 共用同一 Key。

```
Endpoint: https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings
Model: text-embedding-v4
Dimension: 1024
Cost: 约 ¥0.0007/次 (极低成本)
Latency: ~100ms
```

## 核心流程

### 1. 向量生成与存储

```python
# ai_query.py 中新增

class QueryVectorStore:
    """查询向量存储"""

    def __init__(self):
        self.embedding_model = "text-embedding-v4"
        self.threshold = 0.78  # 相似度阈值
        self.max_results = 3   # 返回 Top-N

    async def embed(self, text: str) -> list[float]:
        """将文本转为向量"""
        resp = await self._get_client().post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.embedding_model,
                "input": [text],
            }
        )
        return resp.json()["data"][0]["embedding"]

    async def save(self, query: str, sql: str):
        """保存查询及其向量"""
        vector = await self.embed(query)
        execute_update(
            "INSERT INTO query_vectors (query_text, query_vector, sql_result) VALUES (?, ?, ?)",
            (query, json.dumps(vector), sql)
        )

    async def search(self, query: str) -> Optional[dict]:
        """语义搜索，返回最相似的查询+SQL"""
        query_vec = await self.embed(query)

        # 加载所有历史向量
        rows = execute_query("SELECT * FROM query_vectors ORDER BY id DESC LIMIT 1000")

        best_score = 0
        best_match = None

        for row in rows:
            stored_vec = json.loads(row["query_vector"])
            score = cosine_similarity(query_vec, stored_vec)
            if score > best_score:
                best_score = score
                best_match = {
                    "sql": row["sql_result"],
                    "query": row["query_text"],
                    "score": round(score, 3),
                }

        if best_score >= self.threshold:
            return best_match
        return None
```

### 2. Cosine 相似度计算

```python
import math

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算两个向量的余弦相似度"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
```

### 3. Pipeline 集成

```python
async def execute_query_pipeline(question: str) -> QueryResponse:
    # 第 1 层：LRU 缓存
    if question in _lru_cache:
        return _lru_cache[question]

    # 第 2 层：关键词匹配（现有逻辑，0ms）
    keyword_match = match_standard_sql_cached(question)
    if keyword_match:
        thinking["match_source"] = "关键词匹配"
        return keyword_match

    # 第 3 层：向量语义匹配（新增，~200ms）
    vector_match = await vector_store.search(question)
    if vector_match:
        thinking["match_source"] = f"向量语义匹配(score={vector_match['score']})"
        return vector_match

    # 第 4 层：AI LLM 调用（兜底，~60s）
    sql = await bailian_client.generate_sql(question, schema_context)
    # 保存到向量库，供后续复用
    await vector_store.save(question, sql)
    return sql
```

## 效果预估

| 指标 | 当前 | 加入向量后 | 改善 |
|------|------|-----------|------|
| 命中率（非标准库问题） | 0% → 直接调 AI | 40-60% | 显著 |
| 平均响应时间 | ~30s（全部走 AI） | ~5s（部分命中向量） | 6x |
| LLM Token 消耗 | 每次 ~7000 tokens | 减少 40-60% | 显著 |
| 新增查询延迟 | - | ~200ms（embedding 计算） | 可接受 |

## 与 SQL-Soul 项目的差异

SQL-Soul 项目中已实现类似的向量匹配：
- 使用 `quiz-vector-store.js` 实现余弦相似度
- 阈值 0.78 + 间距 0.04 门控
- 启动时自动同步向量索引

erp-bi-system 可以复用这个模式，但有几个不同点：
1. **向量内容不同**：SQL-Soul 是游戏意图描述，erp-bi 是自然语言查询
2. **数据量更大**：erp-bi 的历史查询会持续增长，需要 TOP-N 限制
3. **需要实时写入**：每次 AI 生成的新 SQL 要自动入库

## 实施步骤

1. 创建 `query_vectors` 表（MySQL/SQLite 均可）
2. 实现 `QueryVectorStore` 类
3. 在 `execute_query` 的关键词匹配和 AI 调用之间插入向量层
4. 迁移现有标准 SQL 库到向量库（一次性初始化）
5. 监控命中率，调整阈值（建议初始 0.78）

## 扩展：混合匹配

更激进的方案：关键词匹配 + 向量匹配同时运行，取分数高的。

```python
keyword_score = calculate_keyword_score(question, candidate)
vector_score = cosine_similarity(query_vec, candidate_vec)
combined_score = keyword_score * 0.3 + vector_score * 0.7
```

这样即使关键词分数低，但语义相似的查询也能被召回。
