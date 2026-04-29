"""
AI 问数记录 API
提供查询历史记录、统计分析、异常监控等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import json
import re

from api.database import execute_query, execute_update, get_db_connection
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/ai-query", tags=["后台管理 - AI 问数记录"])
router_portal = APIRouter(prefix="/api/portal/ai-query", tags=["前台 - AI 问数"])
router_standard = APIRouter(prefix="/api/admin/standard-sql", tags=["后台管理 - 标准 SQL 库"])

security = HTTPBearer()


def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证管理员权限"""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("sub"), "payload": payload}
    except HTTPException:
        raise HTTPException(status_code=401, detail="未授权或 token 已过期")


def get_current_portal_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证前台用户"""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        user = execute_query("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        return user[0]
    except HTTPException:
        raise HTTPException(status_code=401, detail="未授权或 token 已过期")


# ===========================================
# 请求模型
# ===========================================

class QueryRequest(BaseModel):
    """查询请求"""
    question: str
    top_k: int = 10


class StandardSQLSyncRequest(BaseModel):
    """同步标准 SQL 请求"""
    question_template: Optional[str] = None
    standard_sql: Optional[str] = None
    explanation: Optional[str] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[int] = 1
    overwrite: bool = True


# ===========================================
# 辅助函数
# ===========================================

def load_ai_config() -> Dict[str, Any]:
    """加载 AI 配置"""
    config_file = "config/ai_config.json"
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
            "base_url": "https://dashscope.aliyuncs.com/api/v1",
            "model": "qwen-plus",
            "sensitive_words": "DROP, DELETE, TRUNCATE",
            "sensitive_tables": ["users", "roles"],
            "daily_quota": 100
        }


def check_sensitive_content(question: str, sql: str = "") -> Optional[str]:
    """检查敏感内容"""
    config = load_ai_config()

    # 检查敏感词
    sensitive_words = config.get("sensitive_words", "").split(",")
    for word in sensitive_words:
        word = word.strip().upper()
        if word and (word in question.upper() or word in sql.upper()):
            return f"检测到敏感词：{word}"

    # 检查危险 SQL 操作
    dangerous_patterns = [
        r'\bDROP\b', r'\bDELETE\b', r'\bTRUNCATE\b',
        r'\bINSERT\b', r'\bUPDATE\b', r'\bGRANT\b',
        r'\bREVOKE\b', r'\bALTER\b'
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, sql, re.IGNORECASE):
            return f"检测到危险 SQL 操作"

    # 检查敏感表
    sensitive_tables = config.get("sensitive_tables", [])
    for table in sensitive_tables:
        if table and table.lower() in sql.lower():
            return f"访问受限表：{table}"

    return None


def convert_mysql_to_sqlite(sql: str) -> str:
    """
    MySQL SQL 语法转换为 SQLite 兼容语法
    """
    import re
    
    result = sql
    
    # 1. 日期时间函数
    result = re.sub(r'\bNOW\(\)', "datetime('now', 'localtime')", result, flags=re.IGNORECASE)
    result = re.sub(r'\bCURDATE\(\)', "date('now')", result, flags=re.IGNORECASE)
    result = re.sub(r'\bCURRENT_DATE\b', "date('now')", result, flags=re.IGNORECASE)
    result = re.sub(r'\bCURRENT_TIMESTAMP\b', "datetime('now', 'localtime')", result, flags=re.IGNORECASE)
    
    # 2. DATE_SUB/DATE_ADD
    result = re.sub(r'DATE_SUB\(\s*CURDATE\(\)\s*,\s*INTERVAL\s+(\d+)\s+MONTH\)', r"datetime('now', '-\1 month')", result, flags=re.IGNORECASE)
    result = re.sub(r'DATE_SUB\(\s*CURDATE\(\)\s*,\s*INTERVAL\s+(\d+)\s+DAY\)', r"datetime('now', '-\1 day')", result, flags=re.IGNORECASE)
    result = re.sub(r'DATE_SUB\(\s*CURDATE\(\)\s*,\s*INTERVAL\s+(\d+)\s+YEAR\)', r"datetime('now', '-\1 year')", result, flags=re.IGNORECASE)
    result = re.sub(r'DATE_SUB\(\s*CURDATE\(\)\s*,\s*INTERVAL\s+1\s+MONTH\)', "datetime('now', '-1 month')", result, flags=re.IGNORECASE)
    result = re.sub(r'DATE_SUB\(\s*CURDATE\(\)\s*,\s*INTERVAL\s+1\s+DAY\)', "datetime('now', '-1 day')", result, flags=re.IGNORECASE)
    
    result = re.sub(r'DATE_ADD\(\s*CURDATE\(\)\s*,\s*INTERVAL\s+(\d+)\s+MONTH\)', r"datetime('now', '+\1 month')", result, flags=re.IGNORECASE)
    result = re.sub(r'DATE_ADD\(\s*CURDATE\(\)\s*,\s*INTERVAL\s+(\d+)\s+DAY\)', r"datetime('now', '+\1 day')", result, flags=re.IGNORECASE)
    
    # 3. 日期提取函数
    result = re.sub(r'\bYEAR\(([^)]+)\)', "strftime('%Y', \\1)", result, flags=re.IGNORECASE)
    result = re.sub(r'\bMONTH\(([^)]+)\)', "strftime('%m', \\1)", result, flags=re.IGNORECASE)
    result = re.sub(r'\bDAY\(([^)]+)\)', "strftime('%d', \\1)", result, flags=re.IGNORECASE)
    result = re.sub(r'\bDATE\(([^)]+)\)', "date(\\1)", result, flags=re.IGNORECASE)
    result = re.sub(r'\bDATETIME\(([^)]+)\)', "datetime(\\1)", result, flags=re.IGNORECASE)
    
    # DATE_FORMAT 转换（常用格式）
    result = re.sub(r"DATE_FORMAT\(([^,]+),\s*'%Y-%m'\)", "strftime('%Y-%m', \\1)", result, flags=re.IGNORECASE)
    result = re.sub(r"DATE_FORMAT\(([^,]+),\s*'%Y-%m-%d'\)", "strftime('%Y-%m-%d', \\1)", result, flags=re.IGNORECASE)
    result = re.sub(r"DATE_FORMAT\(([^,]+),\s*'%Y'\)", "strftime('%Y', \\1)", result, flags=re.IGNORECASE)
    result = re.sub(r"DATE_FORMAT\(([^,]+),\s*'%m'\)", "strftime('%m', \\1)", result, flags=re.IGNORECASE)
    result = re.sub(r"DATE_FORMAT\(([^,]+),\s*'%d'\)", "strftime('%d', \\1)", result, flags=re.IGNORECASE)
    
    # 4. 其他函数
    result = re.sub(r'\bIFNULL\(', 'COALESCE(', result, flags=re.IGNORECASE)
    result = re.sub(r'\bGROUP_CONCAT\(([^)]+)\)', 'GROUP_CONCAT(\\1)', result, flags=re.IGNORECASE)
    result = re.sub(r'\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)', r'LIMIT \1 OFFSET \2', result, flags=re.IGNORECASE)
    
    return result


def extract_keywords_from_question(question: str) -> list:
    """从问题中提取关键词"""
    # 定义关键词词典
    table_keywords = [
        '项目', '楼盘', '楼栋', '房源', '单元', '客户', '跟进', '认购', '合同',
        '回款', '应收', '退款', '成本', '财务', '损益', '集团', '科目', '指标',
        '维度', '报表', '销售', '去化', '库存'
    ]
    time_keywords = ['今日', '本月', '上月', '今年', '去年', '最近', '当前', '历史', '昨天', '本周']
    action_keywords = ['查询', '统计', '分析', '汇总', '排行', '排名', '占比', '趋势', '对比', '明细']
    metric_keywords = ['金额', '数量', '销售额', '利润', '成本', '单价', '总计', '平均', '去化率', '回款率']
    
    keywords = []
    for kw in table_keywords + time_keywords + action_keywords + metric_keywords:
        if kw in question:
            keywords.append(kw)
    
    return keywords if keywords else question.split()[:5]


def _normalize_text(value: str) -> str:
    """归一化文本，便于去重匹配"""
    return re.sub(r"\s+", "", (value or "")).strip().lower()


def _normalize_sql(value: str) -> str:
    """归一化 SQL，便于去重匹配"""
    normalized = re.sub(r"\s+", " ", (value or "")).strip().rstrip(";")
    return normalized.lower()


def _parse_keywords(value: Any) -> List[str]:
    """兼容 JSON 字符串 / 列表 / 逗号文本的关键词解析"""
    if not value:
        return []
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                raw_items = parsed
            else:
                raw_items = re.split(r"[,，、\n]+", value)
        except Exception:
            raw_items = re.split(r"[,，、\n]+", value)
    else:
        raw_items = [str(value)]

    keywords = []
    for item in raw_items:
        kw = str(item).strip()
        if kw and kw not in keywords:
            keywords.append(kw)
    return keywords


def _merge_keywords(*keyword_groups: Any) -> List[str]:
    """合并多个关键词列表，并去重保序"""
    merged: List[str] = []
    for group in keyword_groups:
        for kw in _parse_keywords(group):
            if kw not in merged:
                merged.append(kw)
    return merged


def _resolve_match_source(row: Dict[str, Any]) -> str:
    """解析问数来源，兼容旧日志与新日志"""
    raw_source = str(row.get("match_source") or "").strip()
    if raw_source:
        if "拦截" in raw_source:
            return "安全拦截"
        if "标准" in raw_source:
            return "标准库命中"
        if "AI" in raw_source:
            return "AI 在线生成"
        return raw_source

    total_tokens = row.get("total_tokens", 0)
    try:
        total_tokens = int(total_tokens or 0)
    except Exception:
        total_tokens = 0

    if row.get("status") == "success" and total_tokens == 0:
        return "标准库命中"
    return "AI 在线生成"


def _refresh_standard_sql_cache() -> None:
    """刷新 AI 问数侧的标准 SQL 缓存"""
    try:
        from api.ai_query import load_standard_sql_cache

        load_standard_sql_cache()
    except Exception:
        # 记录同步完成不依赖缓存刷新成功
        pass


def _find_standard_sql_match(cursor, question_template: str, standard_sql: str):
    """查找可复用的标准 SQL 记录，避免重复入库"""
    cursor.execute("""
        SELECT id, keywords, question_template, standard_sql, explanation, usage_count, is_active
        FROM standard_sql_library
    """)
    rows = cursor.fetchall()
    normalized_question = _normalize_text(question_template)
    normalized_sql = _normalize_sql(standard_sql)

    for row in rows:
        row_question = _normalize_text(row["question_template"] or "")
        row_sql = _normalize_sql(row["standard_sql"] or "")
        if normalized_question and normalized_question == row_question:
            return row
        if normalized_sql and normalized_sql == row_sql:
            return row

    return None


def match_standard_sql_from_library(keywords: list, question_text: str = "") -> dict:
    """从标准 SQL 库中匹配"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # 查询所有启用的标准 SQL
            cursor.execute("""
                SELECT id, keywords, question_template, standard_sql, explanation, usage_count
                FROM standard_sql_library
                WHERE is_active = 1
                ORDER BY usage_count DESC
            """)
            records = cursor.fetchall()
            normalized_question = _normalize_text(question_text)
            
            # 简单匹配：检查关键词是否有重叠
            for record in records:
                try:
                    lib_keywords = json.loads(record['keywords']) if record['keywords'] else []
                    template_text = _normalize_text(record['question_template'] or "")
                    # 计算匹配度：关键词重叠 + 问题模板相似度
                    match_count = sum(1 for kw in keywords if kw in lib_keywords)
                    score = match_count

                    if normalized_question and template_text:
                        if normalized_question == template_text:
                            score += 4
                        else:
                            score += sum(1 for kw in keywords if kw and kw in template_text)

                    if score >= 2:  # 至少达到基础匹配分
                        # 更新使用次数
                        cursor.execute("""
                            UPDATE standard_sql_library
                            SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (record['id'],))
                        conn.commit()
                        
                        return {
                            'id': record['id'],
                            'sql': record['standard_sql'],
                            'explanation': record['explanation'],
                            'matched': True
                        }
                except:
                    continue
            
            return None
    except:
        return None


def generate_sql_from_question(question: str) -> tuple[str, str, str]:
    """
    根据问题生成 SQL（优先匹配标准 SQL 库）
    """
    import httpx
    import json
    
    # 1. 提取关键词
    keywords = extract_keywords_from_question(question)
    
    # 2. 优先匹配标准 SQL 库
    standard_match = match_standard_sql_from_library(keywords, question)
    if standard_match:
        return standard_match['sql'], f"标准库匹配：{standard_match['explanation']}", "标准库命中"
    
    # 3. 标准库未匹配，调用 AI 生成
    config = load_ai_config()
    api_key = config.get("api_key", "")
    base_url = config.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = config.get("model", "qwen3.5-plus")
    system_prompt = config.get("system_prompt", "")
    user_prompt = config.get("user_prompt", "请将以下问题转换为 SQL 查询：{question}")
    
    # 获取表结构
    table_schemas = config.get("table_schemas", [])
    schema_info = ""
    if table_schemas:
        for table in table_schemas:
            schema_info += f"\n表名：{table.get('table_name')}"
            schema_info += f"\n中文：{table.get('table_alias', '')}"
            schema_info += f"\n描述：{table.get('description', '')}"
            schema_info += "\n字段："
            for field in table.get("fields", []):
                schema_info += f"\n  - {field.get('name')} ({field.get('type', '')})"
    else:
        from api.ai_query import get_schema_context
        schema_info = get_schema_context()

    # 构建提示词
    full_system_prompt = f"""{system_prompt}

数据库表结构：
{schema_info}

要求：
1. 只输出 SQL 语句，不要解释
2. 使用 SQLite 兼容语法
3. 只允许 SELECT 查询
4. 优先使用地产表和报表表"""

    full_user_prompt = user_prompt.format(question=question)

    try:
        # 调用百炼 API（超时 120 秒）
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": full_system_prompt},
                        {"role": "user", "content": full_user_prompt}
                    ],
                    "max_tokens": 2000
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    ai_response = data["choices"][0]["message"]["content"].strip()
                    
                    # 提取 SQL 语句（可能包含```sql 标记）
                    sql = ai_response
                    if "```sql" in ai_response:
                        sql = ai_response.split("```sql")[1].split("```")[0].strip()
                    elif "```" in ai_response:
                        sql = ai_response.split("```")[1].split("```")[0].strip()
                    
                    # MySQL → SQLite 函数转换
                    sql = convert_mysql_to_sqlite(sql)
                    
                    # 验证 SQL 是否有效
                    if sql.upper().startswith("SELECT"):
                        return sql, f"AI 生成：{ai_response[:80]}...", "AI 在线生成"
            
            # API 调用失败，使用规则匹配
            rule_sql, rule_explanation = generate_sql_by_rules(question)
            return rule_sql, rule_explanation, "AI 在线生成"
            
    except httpx.TimeoutException:
        # 超时，使用规则匹配
        rule_sql, rule_explanation = generate_sql_by_rules(question)
        return rule_sql, rule_explanation, "AI 在线生成"
    except Exception as e:
        # 出错，使用规则匹配
        rule_sql, rule_explanation = generate_sql_by_rules(question)
        return rule_sql, rule_explanation, "AI 在线生成"


def generate_sql_by_rules(question: str) -> tuple[str, str]:
    """
    根据关键词匹配生成 SQL（降级方案）
    """
    if any(k in question for k in ["去化", "售罄", "销售"]):
        sql = """SELECT project_name,
                       total_units,
                       sold_units,
                       available_units,
                       sell_through_rate
                FROM ads_sales_dashboard
                ORDER BY sell_through_rate DESC
                LIMIT 10"""
        explanation = "查询项目去化情况"
    elif any(k in question for k in ["签约", "合同"]):
        sql = """SELECT contract_code, contract_date, contract_status, total_price, area, unit_price
                FROM re_contracts
                ORDER BY contract_date DESC
                LIMIT 10"""
        explanation = "查询合同签约明细"
    elif any(k in question for k in ["回款", "收款", "付款"]):
        sql = """SELECT payment_code, payment_date, payment_type, amount, payment_method
                FROM re_payments
                ORDER BY payment_date DESC
                LIMIT 10"""
        explanation = "查询回款明细"
    elif any(k in question for k in ["应收", "逾期", "欠款"]):
        sql = """SELECT receivable_id, receivable_type, amount, due_date, received_amount, balance, overdue_days, status
                FROM re_receivables
                ORDER BY overdue_days DESC, due_date DESC
                LIMIT 10"""
        explanation = "查询应收及逾期情况"
    elif any(k in question for k in ["退款", "退房", "退订"]):
        sql = """SELECT refund_code, refund_amount, refund_type, refund_reason, refund_status, apply_date
                FROM re_refunds
                ORDER BY apply_date DESC
                LIMIT 10"""
        explanation = "查询退款明细"
    elif "客户" in question and any(k in question for k in ["跟进", "回访", "意向"]):
        sql = """SELECT c.customer_name,
                       c.phone,
                       c.source,
                       c.intention_level,
                       f.followup_date,
                       f.followup_type,
                       f.followup_content
                FROM re_customers c
                LEFT JOIN re_customer_followups f ON c.customer_id = f.customer_id
                ORDER BY f.followup_date DESC
                LIMIT 10"""
        explanation = "查询客户跟进记录"
    elif any(k in question for k in ["成本", "预算", "费用"]):
        sql = """SELECT project_name, account_name, cost_type, budget_amount, actual_amount, variance_amount, variance_rate
                FROM ads_project_cost_report
                ORDER BY variance_rate DESC
                LIMIT 10"""
        explanation = "查询项目成本分析"
    else:
        sql = """SELECT project_name, total_units, sold_units, available_units, sell_through_rate
                FROM ads_sales_dashboard
                ORDER BY project_name ASC
                LIMIT 10"""
        explanation = "查询项目销售概览"

    return sql, explanation


def execute_sql_query(sql: str, top_k: int = 10) -> tuple[list, list]:
    """执行 SQL 查询（支持 SQLite 和 MySQL）"""
    import sqlite3
    
    # 使用 SQLite（与 database.py 保持一致）
    db_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'erp_bi.db')
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description] if cursor.description else []
        data = [dict(zip(columns, row)) for row in rows]
        conn.close()
        return data[:top_k], columns
    except Exception as e:
        raise Exception(f"SQL 执行失败：{str(e)}")


def save_query_log(user_id: int, username: str, question: str, sql: str,
                   status: str, execution_time: int = 0,
                   result_count: int = 0, error_message: str = "",
                   match_source: str = "AI 在线生成"):
    """保存查询日志"""
    insert_sql = """
        INSERT INTO ai_query_logs
        (user_id, username, question, generated_sql, status, execution_time_ms, result_count, error_message, match_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    execute_update(insert_sql, (
        user_id, username, question, sql,
        status, execution_time, result_count, error_message, match_source
    ))


# ===========================================
# 后台管理 API
# ===========================================

@router.get("/records")
async def get_query_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    username: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取 AI 查询记录（后台管理）"""
    offset = (page - 1) * page_size

    # 构建查询条件
    where_clauses = []
    params = []

    if username:
        where_clauses.append("username LIKE ?")
        params.append(f"%{username}%")

    if keyword:
        where_clauses.append("(question LIKE ? OR generated_sql LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if status:
        where_clauses.append("status = ?")
        params.append(status)

    if start_date:
        where_clauses.append("DATE(created_at) >= ?")
        params.append(start_date)

    if end_date:
        where_clauses.append("DATE(created_at) <= ?")
        params.append(end_date)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # 查询总数
    count_sql = f"SELECT COUNT(*) as total FROM ai_query_logs WHERE {where_sql}"
    count_result = execute_query(count_sql, tuple(params))
    total = count_result[0]["total"] if count_result else 0

    # 查询记录
    records_sql = f"""
        SELECT * FROM ai_query_logs
        WHERE {where_sql}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    records = execute_query(records_sql, tuple(params))

    items = []
    for row in records:
        keywords = _parse_keywords(row.get("keywords"))
        match_source = _resolve_match_source(row)
        items.append({
            "query_id": row["id"],
            "username": row["username"],
            "question": row["question"],
            "sql": row.get("generated_sql", ""),
            "generated_sql": row.get("generated_sql", ""),
            "keywords": keywords,
            "status": row["status"],
            "match_source": match_source,
            "matched_standard": match_source == "标准库命中",
            "execution_time": row.get("execution_time_ms", row.get("execution_time", 0)),
            "result_count": row.get("result_count", 0),
            "created_at": str(row["created_at"])[:19] if row.get("created_at") else "",
            "error_message": row.get("error_message", "")
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/records/{query_id}/sync-standard-sql")
async def sync_query_record_to_standard_sql(
    query_id: int,
    request: StandardSQLSyncRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """将问数记录同步到标准 SQL 库"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_query_logs WHERE id = ?", (query_id,))
            record = cursor.fetchone()
            if not record:
                raise HTTPException(status_code=404, detail="问数记录不存在")

            source_question = record["question"] or ""
            source_sql = record["generated_sql"] or ""
            source_keywords = _parse_keywords(record["keywords"]) or extract_keywords_from_question(source_question)

            question_template = (request.question_template or source_question or "").strip()
            standard_sql = (request.standard_sql or source_sql or "").strip()
            explanation = (request.explanation or "").strip() or f"由问数记录同步：{source_question[:60]}"
            keywords = _merge_keywords(source_keywords, request.keywords, extract_keywords_from_question(question_template or source_question))
            is_active = 1 if request.is_active is None else int(bool(request.is_active))

            if not question_template:
                raise HTTPException(status_code=400, detail="问题模板不能为空")
            if not standard_sql:
                raise HTTPException(status_code=400, detail="标准 SQL 不能为空")

            matched_row = _find_standard_sql_match(cursor, question_template, standard_sql)
            payload_keywords = json.dumps(keywords, ensure_ascii=False)

            if matched_row:
                update_fields = []
                update_params = []

                existing_keywords = _parse_keywords(matched_row["keywords"])
                merged_keywords = _merge_keywords(existing_keywords, keywords)

                if request.overwrite or not matched_row["question_template"]:
                    update_fields.append("question_template = ?")
                    update_params.append(question_template)
                if request.overwrite or not matched_row["standard_sql"]:
                    update_fields.append("standard_sql = ?")
                    update_params.append(standard_sql)
                if request.overwrite or request.explanation is not None or not matched_row["explanation"]:
                    update_fields.append("explanation = ?")
                    update_params.append(explanation)

                update_fields.append("keywords = ?")
                update_params.append(json.dumps(merged_keywords, ensure_ascii=False))
                update_fields.append("is_active = ?")
                update_params.append(is_active)
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                update_params.append(matched_row["id"])

                cursor.execute(
                    f"UPDATE standard_sql_library SET {', '.join(update_fields)} WHERE id = ?",
                    update_params
                )
                action = "updated"
                sql_id = matched_row["id"]
            else:
                cursor.execute("""
                    INSERT INTO standard_sql_library
                    (keywords, question_template, standard_sql, explanation, usage_count, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 0, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    payload_keywords,
                    question_template,
                    standard_sql,
                    explanation,
                    is_active
                ))
                action = "created"
                sql_id = cursor.lastrowid

            conn.commit()
            _refresh_standard_sql_cache()

            return {
                "message": "同步成功",
                "action": action,
                "standard_sql_id": sql_id,
                "question_template": question_template,
                "standard_sql": standard_sql
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_query_stats(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取查询统计"""
    from api.ai_config import load_ai_config

    config = load_ai_config()
    today = datetime.now().strftime('%Y-%m-%d')

    total_result = execute_query("SELECT COUNT(*) as count FROM ai_query_logs")
    total = total_result[0]["count"] if total_result else 0

    success_result = execute_query("SELECT COUNT(*) as count FROM ai_query_logs WHERE status = 'success'")
    success = success_result[0]["count"] if success_result else 0

    failed = total - success
    rate = round(success * 100 / total, 1) if total > 0 else 0

    today_result = execute_query("""
        SELECT COUNT(*) as count,
               SUM(CASE WHEN COALESCE(match_source, '') LIKE '%标准%' THEN 1 ELSE 0 END) as standard_hits,
               SUM(CASE WHEN COALESCE(match_source, '') LIKE '%AI%' THEN 1 ELSE 0 END) as ai_generated,
               AVG(CASE WHEN status = 'success' THEN execution_time_ms END) as avg_time
        FROM ai_query_logs
        WHERE DATE(created_at) = ?
    """, (today,))
    today_row = today_result[0] if today_result else {}

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "rate": rate,
        "today_count": today_row.get("count", 0) if today_row else 0,
        "standard_hits": today_row.get("standard_hits", 0) if today_row else 0,
        "ai_generated": today_row.get("ai_generated", 0) if today_row else 0,
        "avg_time": round(today_row.get("avg_time", 0) or 0, 2) if today_row else 0,
        "daily_quota": config.get("daily_quota", 100),
        "remaining": max(0, config.get("daily_quota", 100) - (today_row.get("count", 0) if today_row else 0))
    }


@router.get("/trend")
async def get_query_trend(
    days: int = Query(default=7, ge=1, le=30),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取查询趋势（SQLite 版本）"""
    result = execute_query("""
        SELECT DATE(created_at) as date, COUNT(*) as count,
               SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count
        FROM ai_query_logs
        WHERE created_at >= datetime('now', '-' || ? || ' days')
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """, (days,))

    trend = []
    for row in result:
        trend.append({
            "date": str(row["date"]),
            "count": row["count"],
            "success_count": row["success_count"]
        })

    return {"days": days, "data": trend}


# ===========================================
# 前台 API
# ===========================================

@router_portal.post("/execute")
async def execute_portal_query(
    request: QueryRequest,
    current_user: dict = Depends(get_current_portal_user)
):
    """执行 AI 查询（前台）"""
    import time

    user_id = current_user["user_id"]
    username = current_user["username"]

    # 检查用户 AI 权限
    if not current_user.get("ai_enabled", 1):
        raise HTTPException(status_code=403, detail="AI 问数功能已被禁用")

    # 检查今日配额
    quota = current_user.get("ai_quota", 100)
    used = current_user.get("ai_used_today", 0)
    if used >= quota:
        raise HTTPException(status_code=429, detail="今日查询配额已用完")

    # 检查敏感内容
    sensitive_msg = check_sensitive_content(request.question)
    if sensitive_msg:
        save_query_log(user_id, username, request.question, "", "error",
                       0, 0, sensitive_msg, "安全拦截")
        raise HTTPException(status_code=400, detail=sensitive_msg)

    start_time = time.time()

    try:
        # 生成 SQL
        sql, explanation, match_source = generate_sql_from_question(request.question)

        # 再次检查生成的 SQL
        sensitive_msg = check_sensitive_content(request.question, sql)
        if sensitive_msg:
            save_query_log(user_id, username, request.question, sql, "error",
                           0, 0, sensitive_msg, "安全拦截")
            raise HTTPException(status_code=400, detail=sensitive_msg)

        # 执行查询
        data, columns = execute_sql_query(sql, request.top_k)

        execution_time = int((time.time() - start_time) * 1000)

        # 保存成功日志
        save_query_log(user_id, username, request.question, sql, "success",
                       execution_time, len(data), "", match_source)

        # 更新用户使用量
        execute_update("UPDATE users SET ai_used_today = ai_used_today + 1 WHERE user_id = ?", (user_id,))

        return {
            "sql": sql,
            "explanation": explanation,
            "data": data,
            "columns": columns
        }

    except HTTPException:
        raise
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        save_query_log(user_id, username, request.question, "", "error",
                       execution_time, 0, str(e), match_source if 'match_source' in locals() else "安全拦截")
        raise HTTPException(status_code=500, detail=str(e))


@router_portal.get("/quota")
async def get_user_quota(
    current_user: dict = Depends(get_current_portal_user)
):
    """获取用户配额信息"""
    user_id = current_user["user_id"]

    user = execute_query("SELECT ai_quota, ai_used_today FROM users WHERE user_id = ?", (user_id,))
    if user:
        return {
            "daily": user[0].get("ai_quota", 100),
            "used": user[0].get("ai_used_today", 0),
            "remaining": max(0, user[0].get("ai_quota", 100) - user[0].get("ai_used_today", 0))
        }

    return {"daily": 100, "used": 0, "remaining": 100}


@router_portal.get("/history")
async def get_user_history(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_portal_user)
):
    """获取用户查询历史"""
    user_id = current_user["user_id"]

    result = execute_query("""
        SELECT question, sql, status, created_at
        FROM ai_query_logs
        WHERE user_id = ?
        ORDER BY query_id DESC
        LIMIT ?
    """, (user_id, limit))

    history = []
    for row in result:
        history.append({
            "question": row["question"],
            "sql": row["sql"],
            "status": row["status"],
            "time": str(row["created_at"])[:16] if row.get("created_at") else ""
        })

    return {"history": history}


# ===========================================
# 标准 SQL 库管理 API
# ===========================================

@router_standard.get("")
async def list_standard_sql(
    keywords: Optional[str] = None,
    is_active: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取标准 SQL 列表（后台管理）"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 构建 WHERE 子句
            where_clauses = []
            params = []
            
            if keywords:
                where_clauses.append("(question_template LIKE ? OR keywords LIKE ?)")
                keyword_pattern = f"%{keywords}%"
                params.extend([keyword_pattern, keyword_pattern])
            
            if is_active is not None:
                where_clauses.append("is_active = ?")
                params.append(is_active)
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM standard_sql_library WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            # 查询数据
            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT id, keywords, question_template, standard_sql, explanation, usage_count, is_active, created_at, updated_at
                FROM standard_sql_library
                WHERE {where_sql}
                ORDER BY usage_count DESC, id DESC
                LIMIT ? OFFSET ?
            """
            params.extend([page_size, offset])
            cursor.execute(data_sql, params)
            records = cursor.fetchall()
            
            # 统计数据
            cursor.execute("SELECT COUNT(*) as total FROM standard_sql_library")
            stats_total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as active FROM standard_sql_library WHERE is_active = 1")
            stats_active = cursor.fetchone()['active']
            
            cursor.execute("SELECT SUM(usage_count) as usage_count FROM standard_sql_library")
            stats_usage = cursor.fetchone()['usage_count'] or 0
            
            stats_token_saved = stats_usage * 2000
            
            result = []
            for record in records:
                result.append({
                    'id': record['id'],
                    'keywords': json.loads(record['keywords']) if record['keywords'] else [],
                    'question_template': record['question_template'],
                    'standard_sql': record['standard_sql'],
                    'explanation': record['explanation'],
                    'usage_count': record['usage_count'],
                    'is_active': bool(record['is_active']),
                    'created_at': record['created_at'],
                    'updated_at': record['updated_at']
                })
            
            return {
                "items": result,
                "total": total,
                "page": page,
                "page_size": page_size,
                "stats": {
                    "total": stats_total,
                    "active": stats_active,
                    "usageCount": stats_usage,
                    "tokenSaved": stats_token_saved
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_standard.post("")
async def create_standard_sql(
    request: dict,
    current_user: dict = Depends(get_current_admin_user)
):
    """创建标准 SQL 记录"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO standard_sql_library 
                (keywords, question_template, standard_sql, explanation, usage_count, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                json.dumps(request.get('keywords', []), ensure_ascii=False),
                request.get('question_template', ''),
                request.get('standard_sql', ''),
                request.get('explanation', '')
            ))
            return {"id": cursor.lastrowid, "message": "创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_standard.put("/{sql_id}")
async def update_standard_sql(
    sql_id: int,
    request: dict,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新标准 SQL 记录"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if 'keywords' in request:
                updates.append("keywords = ?")
                params.append(json.dumps(request['keywords'], ensure_ascii=False))
            if 'question_template' in request:
                updates.append("question_template = ?")
                params.append(request['question_template'])
            if 'standard_sql' in request:
                updates.append("standard_sql = ?")
                params.append(request['standard_sql'])
            if 'explanation' in request:
                updates.append("explanation = ?")
                params.append(request['explanation'])
            if 'is_active' in request:
                updates.append("is_active = ?")
                params.append(request['is_active'])
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                set_sql = ", ".join(updates)
                params.append(sql_id)
                cursor.execute(f"UPDATE standard_sql_library SET {set_sql} WHERE id = ?", params)
            
            return {"message": "更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_standard.delete("/{sql_id}")
async def delete_standard_sql(
    sql_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除标准 SQL 记录"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM standard_sql_library WHERE id = ?", (sql_id,))
            return {"message": "删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
