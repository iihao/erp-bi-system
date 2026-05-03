#!/usr/bin/env python3
"""
向量语义匹配层 - 用于 AI 问数语义缓存
借鉴 SQL-Soul 的 quiz-vector-store.js 实现模式：
- 余弦相似度计算
- 问题归一化（去除礼貌用语、语气词）
- 阈值 0.78 + 间距 0.04 门控
- 启动时向量索引同步
"""

import json
import math
import logging
import httpx
from typing import Optional, Dict, Any, List
from api.database import execute_query, execute_update

logger = logging.getLogger(__name__)

# 配置
EMBEDDING_MODEL = "text-embedding-v4"
EMBEDDING_DIM = 1024
SIMILARITY_THRESHOLD = 0.78
MARGIN = 0.04  # 第二名与第一名的最小间距
MAX_VECTORS = 1000  # 内存中保留的历史向量上限


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def normalize_question(question: str) -> str:
    """问题归一化：去除礼貌用语、语气词、标点，提高匹配准确率"""
    q = question.strip()

    # 去除礼貌用语
    polite_words = ["请", "请问", "麻烦", "帮我", "帮忙", "您好", "你好", "hi", "hello"]
    for word in polite_words:
        if q.startswith(word):
            q = q[len(word):].strip()

    # 去除句末语气词和标点
    end_particles = ["呢", "吗", "吧", "啊", "呀", "哦", "哈", "啦"]
    for particle in end_particles:
        if q.endswith(particle):
            q = q[: -len(particle)].strip()

    # 去除句末标点
    q = q.rstrip("？?。！!,")

    return q.strip().lower()


async def embed_text(text: str, api_key: str, base_url: str) -> List[float]:
    """调用 DashScope Embedding API 将文本转为向量。

    注意：sk-sp-* 编码计划专用 Key 不支持 Embedding API。
    使用此类 Key 时向量功能将自动降级为仅关键词匹配模式。
    """
    # 编码计划 Key 不支持 Embedding，直接抛出明确的错误
    if api_key.startswith("sk-sp-"):
        raise Exception("编码计划 Key (sk-sp-*) 不支持 Embedding API，请使用标准 DashScope Key (sk-*)")

    # 标准 DashScope Embedding 端点
    embed_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": EMBEDDING_MODEL,
        "input": [text],
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=2.0)) as client:
        resp = await client.post(embed_url, headers=headers, json=payload)
        if resp.status_code != 200:
            logger.error(f"❌ Embedding 失败：{resp.status_code} - {resp.text[:200]}")
            raise Exception(f"Embedding API error: {resp.status_code}")
        data = resp.json()
        return data["data"][0]["embedding"]


class QueryVectorStore:
    """查询向量存储与匹配"""

    def __init__(self):
        self.enabled = False
        self._vector_cache: List[Dict[str, Any]] = []  # 内存中的向量缓存

    async def sync(self, api_key: str, base_url: str):
        """启动时同步向量索引：从数据库加载已有向量，缺失的重新生成"""
        # 编码计划 Key 不支持 Embedding，直接跳过
        if api_key.startswith("sk-sp-"):
            logger.info("⚠️ 编码计划 Key (sk-sp-*) 不支持 Embedding API，向量匹配已禁用。如需启用请更换为标准 DashScope Key")
            self.enabled = False
            return

        try:
            rows = execute_query(
                "SELECT id, query_text, query_vector, sql_result, explanation FROM query_vectors ORDER BY id DESC LIMIT ?",
                (MAX_VECTORS,)
            )

            loaded = 0
            needs_embed = []

            for row in rows:
                try:
                    vector = json.loads(row["query_vector"])
                    self._vector_cache.append({
                        "id": row["id"],
                        "query_text": row["query_text"],
                        "vector": vector,
                        "sql_result": row["sql_result"],
                        "explanation": row.get("explanation", ""),
                    })
                    loaded += 1
                except (json.JSONDecodeError, KeyError):
                    needs_embed.append(row)

            # 为向量损坏的记录重新生成
            for row in needs_embed:
                try:
                    vector = await embed_text(row["query_text"], api_key, base_url)
                    execute_update(
                        "UPDATE query_vectors SET query_vector = ? WHERE id = ?",
                        (json.dumps(vector), row["id"])
                    )
                    self._vector_cache.append({
                        "id": row["id"],
                        "query_text": row["query_text"],
                        "vector": vector,
                        "sql_result": row["sql_result"],
                        "explanation": row.get("explanation", ""),
                    })
                    loaded += 1
                except Exception as e:
                    logger.warning(f"⚠️ 向量重新生成失败 (id={row['id']})：{e}")

            self.enabled = True
            logger.info(f"✅ 向量索引已同步：{loaded} 条")

        except Exception as e:
            logger.warning(f"⚠️ 向量索引同步失败：{e}，向量匹配将被跳过")
            self.enabled = False

    async def save(self, question: str, sql: str, explanation: str, api_key: str, base_url: str):
        """保存查询及其向量（AI 生成新 SQL 后调用）"""
        if not self.enabled:
            return

        try:
            normalized = normalize_question(question)
            vector = await embed_text(normalized, api_key, base_url)

            execute_update(
                "INSERT INTO query_vectors (query_text, query_vector, sql_result, explanation) VALUES (?, ?, ?, ?)",
                (question, json.dumps(vector), sql, explanation)
            )

            # 同步到内存缓存
            self._vector_cache.append({
                "query_text": question,
                "vector": vector,
                "sql_result": sql,
                "explanation": explanation,
            })

            # 限制内存缓存大小
            if len(self._vector_cache) > MAX_VECTORS:
                self._vector_cache = self._vector_cache[-MAX_VECTORS:]

            logger.info(f"💾 向量已保存：{question[:30]}...")

        except Exception as e:
            logger.warning(f"⚠️ 向量保存失败：{e}")

    async def search(self, question: str) -> Optional[Dict[str, Any]]:
        """语义搜索，返回最匹配的查询+SQL"""
        if not self.enabled or not self._vector_cache:
            return None

        try:
            normalized = normalize_question(question)
            # 完全相同的归一化问题直接返回
            for item in self._vector_cache:
                if normalize_question(item["query_text"]) == normalized:
                    return {
                        "sql": item["sql_result"],
                        "explanation": item.get("explanation", "向量语义匹配（完全相同）"),
                        "match_query": item["query_text"],
                        "score": 1.0,
                    }

            # 计算相似度
            # 注意：这里需要获取 embedding，但我们没有 api_key 在此方法中
            # 改为延迟计算：在调用方传入
            return None  # 占位，实际搜索由 search_with_embedding 完成

        except Exception as e:
            logger.warning(f"⚠️ 向量搜索失败：{e}")
            return None

    async def search_with_embedding(
        self, question: str, question_embedding: List[float]
    ) -> Optional[Dict[str, Any]]:
        """使用已计算的向量进行语义搜索"""
        if not self.enabled or not self._vector_cache:
            return None

        try:
            best_score = 0
            best_match = None
            second_score = 0

            for item in self._vector_cache:
                score = cosine_similarity(question_embedding, item["vector"])
                if score > best_score:
                    second_score = best_score
                    best_score = score
                    best_match = item

            # 门控：相似度 >= 阈值 且 与第二名有足够间距
            if best_score >= SIMILARITY_THRESHOLD and (best_score - second_score) >= MARGIN:
                return {
                    "sql": best_match["sql_result"],
                    "explanation": best_match.get("explanation", "向量语义匹配"),
                    "match_query": best_match["query_text"],
                    "score": round(best_score, 3),
                }

            if best_score >= SIMILARITY_THRESHOLD:
                logger.info(f"⚠️ 向量匹配分数 {best_score:.3f} 达标，但间距不足 ({best_score - second_score:.3f} < {MARGIN})")

            return None

        except Exception as e:
            logger.warning(f"⚠️ 向量搜索失败：{e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """获取向量库统计"""
        return {
            "enabled": self.enabled,
            "vector_count": len(self._vector_cache),
            "max_vectors": MAX_VECTORS,
            "threshold": SIMILARITY_THRESHOLD,
            "margin": MARGIN,
        }


# 全局单例
vector_store = QueryVectorStore()
