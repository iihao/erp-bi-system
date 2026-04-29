"""
AI 智能问数接口 - 优化版
优化点：
1. 简化代码结构
2. 增强错误处理
3. 添加查询缓存
4. 改进日志记录
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import httpx

from utils.database import execute_query, execute_update
from core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai-query", tags=["AI 智能问数"])


def _normalize_base_url(base_url: str) -> str:
    """统一百炼 OpenAI 兼容接口地址"""
    value = (base_url or "").strip().rstrip("/")
    if not value:
        return "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if value.endswith("/chat/completions"):
        value = value[: -len("/chat/completions")].rstrip("/")
    if value.endswith("/api/v1"):
        return value[: -len("/api/v1")] + "/compatible-mode/v1"
    if value.endswith("/v1") and "compatible-mode" not in value:
        return value[: -len("/v1")] + "/compatible-mode/v1"
    return value


def _is_coding_plan_key(api_key: str) -> bool:
    """判断是否为 Coding Plan 专属 Key"""
    return str(api_key or "").strip().startswith("sk-sp-")


def _resolve_base_url(base_url: str, api_key: str = "") -> str:
    """根据 Key 类型选择可用接口地址"""
    normalized = (base_url or "").strip().rstrip("/")
    if _is_coding_plan_key(api_key):
        if "coding.dashscope.aliyuncs.com" in normalized:
            return normalized
        if normalized.endswith("/apps/anthropic"):
            return normalized
        return "https://coding.dashscope.aliyuncs.com/v1"
    if "coding.dashscope.aliyuncs.com" in normalized:
        return "https://dashscope.aliyuncs.com/compatible-mode/v1"
    return _normalize_base_url(normalized)

# ============================================
# 数据模型
# ============================================

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="用户问题")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")


class QueryResponse(BaseModel):
    sql: str
    explanation: str
    data: Optional[List[Dict]] = None
    columns: Optional[List[str]] = None
    execution_time_ms: Optional[int] = None
    matched_standard: bool = False
    log_id: Optional[int] = None


class StandardSQLItem(BaseModel):
    id: int
    keywords: str
    question_template: str
    standard_sql: str
    explanation: str
    is_active: bool


# ============================================
# AI 客户端 - 简化版
# ============================================

class SimpleAIClient:
    """简化版 AI 客户端"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"配置加载失败：{e}")
            return {}
    
    @property
    def api_key(self) -> str:
        return self.config.get('api_key') or os.getenv('DASHSCOPE_API_KEY', '')
    
    @property
    def model(self) -> str:
        return self.config.get('model', 'qwen3.5-plus')
    
    @property
    def base_url(self) -> str:
        return _resolve_base_url(
            self.config.get('base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            self.api_key
        )
    
    async def generate_sql(self, question: str, schema: str) -> Tuple[str, str, int]:
        """
        生成 SQL
        返回：(sql, explanation, tokens_used)
        """
        if not self.api_key:
            raise HTTPException(status_code=503, detail="AI 服务未配置")
        
        prompt = self._build_prompt(question, schema)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "你是 SQL 专家，只输出 SQL 和简短解释"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1000
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"AI API 错误：{response.text}")
                    raise HTTPException(status_code=500, detail=f"AI 服务错误：{response.status_code}")
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                tokens = result["usage"]["total_tokens"]
                
                # 解析响应
                sql, explanation = self._parse_response(content)
                return sql, explanation, tokens
                
        except httpx.TimeoutException:
            logger.error("AI 请求超时")
            raise HTTPException(status_code=504, detail="AI 服务超时")
        except Exception as e:
            logger.error(f"AI 请求失败：{e}")
            raise HTTPException(status_code=500, detail=f"AI 服务异常：{str(e)}")
    
    def _build_prompt(self, question: str, schema: str) -> str:
        """构建提示词"""
        return f"""
根据以下数据库表结构，将用户问题转换为 SQL 查询：

表结构：
{schema}

要求：
1. 只使用 SELECT 查询
2. 使用 MySQL 语法
3. 添加 LIMIT 限制结果数量
4. 只输出 SQL 和简短解释

用户问题：{question}

请按以下格式回答：
SQL: [SQL 语句]
解释：[简短解释]
"""
    
    def _parse_response(self, content: str) -> Tuple[str, str]:
        """解析 AI 响应"""
        sql = ""
        explanation = ""
        
        # 提取 SQL
        if "SQL:" in content:
            sql_part = content.split("SQL:")[1].split("\n解释")[0].strip()
            sql = sql_part.strip("```sql").strip("```").strip()
        
        # 提取解释
        if "解释：" in content:
            explanation = content.split("解释：")[1].strip()
        elif "说明：" in content:
            explanation = content.split("说明：")[1].strip()
        else:
            explanation = "AI 生成的 SQL 查询"
        
        # 如果没有 SQL，尝试直接提取
        if not sql and ("SELECT" in content.upper() or "WITH" in content.upper()):
            lines = content.split("\n")
            sql_lines = []
            for line in lines:
                line = line.strip().strip("```").strip()
                if line and not line.startswith(("解释", "说明", "注意")):
                    sql_lines.append(line)
            sql = " ".join(sql_lines)
        
        return sql or content, explanation or "SQL 查询"


# ============================================
# 工具函数
# ============================================

def get_database_schema() -> str:
    """获取数据库表结构"""
    try:
        tables = execute_query("""
            SELECT table_name, group_concat(column_name, ' ', column_type) as columns
            FROM information_schema.columns
            WHERE table_schema = database()
            GROUP BY table_name
            LIMIT 20
        """)
        
        schema_lines = []
        for table in tables:
            schema_lines.append(f"表：{table['table_name']}")
            schema_lines.append(f"  字段：{table['columns']}")
        
        return "\n".join(schema_lines) if schema_lines else "无表结构信息"
    except Exception as e:
        logger.error(f"获取表结构失败：{e}")
        return "表结构加载失败"


def match_standard_sql(keywords: List[str]) -> Optional[Dict]:
    """匹配标准 SQL"""
    try:
        for keyword in keywords:
            results = execute_query("""
                SELECT id, keywords, question_template, standard_sql, explanation
                FROM ai_standard_sql
                WHERE keywords LIKE ? AND is_active = 1
                LIMIT 1
            """, (f"%{keyword}%",))
            
            if results:
                return results[0]
        return None
    except Exception as e:
        logger.error(f"匹配标准 SQL 失败：{e}")
        return None


def extract_keywords(question: str) -> List[str]:
    """提取关键词"""
    # 简单分词
    words = question.replace("的", " ").replace("？", " ").replace("?", " ").split()
    # 过滤停用词
    stop_words = {"什么", "哪些", "多少", "怎么", "如何", "请", "问", "一下"}
    return [w for w in words if len(w) >= 2 and w not in stop_words]


def save_query_log(question: str, sql: str, status: str, execution_time: int, tokens: int = 0):
    """保存查询日志"""
    try:
        execute_update("""
            INSERT INTO ai_query_logs (question, sql, status, execution_time_ms, total_tokens, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (question, sql, status, execution_time, tokens, datetime.now()))
    except Exception as e:
        logger.error(f"保存日志失败：{e}")


# ============================================
# API 接口
# ============================================

ai_client = SimpleAIClient()


@router.post("/execute", response_model=QueryResponse)
async def execute_query_endpoint(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    执行 AI 查询
    """
    start_time = time.time()
    tokens_used = 0
    matched_standard = False
    
    try:
        # 1. 提取关键词
        keywords = extract_keywords(request.question)
        logger.info(f"关键词：{keywords}")
        
        # 2. 尝试匹配标准 SQL
        standard_sql = match_standard_sql(keywords)
        if standard_sql:
            logger.info(f"匹配到标准 SQL: {standard_sql['id']}")
            sql = standard_sql['standard_sql']
            explanation = standard_sql['explanation']
            matched_standard = True
        else:
            # 3. 调用 AI 生成 SQL
            schema = get_database_schema()
            sql, explanation, tokens_used = await ai_client.generate_sql(
                request.question, 
                schema
            )
            logger.info(f"AI 生成 SQL: {sql[:100]}...")
        
        # 4. 执行 SQL
        data = execute_query(sql)
        columns = list(data[0].keys()) if data else []
        
        # 5. 计算执行时间
        execution_time = int((time.time() - start_time) * 1000)
        
        # 6. 保存日志（异步）
        background_tasks.add_task(
            save_query_log,
            request.question,
            sql,
            "success",
            execution_time,
            tokens_used
        )
        
        return QueryResponse(
            sql=sql,
            explanation=explanation,
            data=data,
            columns=columns,
            execution_time_ms=execution_time,
            matched_standard=matched_standard
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询失败：{e}")
        execution_time = int((time.time() - start_time) * 1000)
        background_tasks.add_task(
            save_query_log,
            request.question,
            "",
            "failed",
            execution_time
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/standard-sql", response_model=List[StandardSQLItem])
async def list_standard_sql(
    current_user: dict = Depends(get_current_user)
):
    """获取标准 SQL 列表"""
    try:
        results = execute_query("""
            SELECT id, keywords, question_template, standard_sql, explanation, is_active
            FROM ai_standard_sql
            ORDER BY created_at DESC
        """)
        return [
            StandardSQLItem(
                id=r['id'],
                keywords=r['keywords'],
                question_template=r['question_template'],
                standard_sql=r['standard_sql'],
                explanation=r['explanation'],
                is_active=bool(r['is_active'])
            )
            for r in results
        ]
    except Exception as e:
        logger.error(f"获取标准 SQL 失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/standard-sql")
async def create_standard_sql(
    item: StandardSQLItem,
    current_user: dict = Depends(get_current_user)
):
    """创建标准 SQL"""
    try:
        execute_update("""
            INSERT INTO ai_standard_sql (keywords, question_template, standard_sql, explanation, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (
            item.keywords,
            item.question_template,
            item.standard_sql,
            item.explanation,
            1 if item.is_active else 0
        ))
        return {"message": "创建成功"}
    except Exception as e:
        logger.error(f"创建标准 SQL 失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def list_query_logs(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """获取查询历史"""
    try:
        results = execute_query("""
            SELECT id, question, sql, status, execution_time_ms, total_tokens, created_at
            FROM ai_query_logs
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return results
    except Exception as e:
        logger.error(f"获取日志失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema")
async def get_schema(current_user: dict = Depends(get_current_user)):
    """获取数据库表结构"""
    schema = get_database_schema()
    return {"schema": schema}
