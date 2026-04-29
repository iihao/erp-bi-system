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

from api.database import execute_query, execute_update
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/ai-records", tags=["后台管理 - AI 问数记录"])
router_portal = APIRouter(prefix="/api/portal/ai-query", tags=["前台 - AI 问数"])

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


def generate_sql_from_question(question: str) -> tuple[str, str]:
    """
    根据问题生成 SQL（简化版本，实际应该调用 AI 服务）
    这里提供一个简单的映射逻辑
    """
    config = load_ai_config()

    # 实际应该调用百炼 API
    # 这里使用简单的关键词匹配作为演示

    question_lower = question.lower()

    if "销售" in question and "最高" in question:
        sql = """SELECT p.product_name, SUM(soi.subtotal) as total_sales
                FROM products p
                JOIN sales_order_items soi ON p.id = soi.product_id
                JOIN sales_orders so ON soi.order_id = so.id
                GROUP BY p.id, p.product_name
                ORDER BY total_sales DESC
                LIMIT 10"""
        explanation = "查询产品销售排名"
    elif "客户" in question and "订单" in question:
        sql = """SELECT so.*, c.customer_name
                FROM sales_orders so
                JOIN customers c ON so.customer_id = c.id
                WHERE c.customer_name LIKE '%张三%'
                ORDER BY so.order_date DESC"""
        explanation = "查询客户订单"
    elif "占比" in question or "比例" in question:
        sql = """SELECT p.category,
                       SUM(soi.subtotal) as category_sales,
                       ROUND(SUM(soi.subtotal) * 100.0 / (SELECT SUM(subtotal) FROM sales_order_items), 2) as percentage
                FROM products p
                JOIN sales_order_items soi ON p.id = soi.product_id
                GROUP BY p.category
                ORDER BY category_sales DESC"""
        explanation = "查询品类销售占比"
    elif "销售额" in question or "金额" in question:
        sql = """SELECT SUM(final_amount) as total_sales
                FROM sales_orders
                WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"""
        explanation = "查询月度销售额"
    elif "库存" in question:
        sql = """SELECT p.product_name, p.stock_quantity
                FROM products p
                ORDER BY p.stock_quantity ASC
                LIMIT 10"""
        explanation = "查询库存最少的产品"
    else:
        sql = """SELECT * FROM sales_orders ORDER BY order_date DESC LIMIT 10"""
        explanation = "查询最新订单"

    return sql, explanation


def execute_sql_query(sql: str, top_k: int = 10) -> tuple[list, list]:
    """执行 SQL 查询"""
    from sqlalchemy import create_engine, text

    db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://erp_bi_user:erp_bi_pass@localhost:3306/erp_bi')

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            columns = list(result.keys())
            data = [dict(zip(columns, row)) for row in rows]
            return data[:top_k], columns
    except Exception as e:
        raise Exception(f"SQL 执行失败：{str(e)}")


def save_query_log(user_id: int, username: str, question: str, sql: str,
                   status: str, execution_time: int = 0,
                   result_count: int = 0, error_message: str = ""):
    """保存查询日志"""
    insert_sql = """
        INSERT INTO ai_query_logs
        (user_id, username, question, sql, status, execution_time, result_count, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    execute_update(insert_sql, (
        user_id, username, question, sql,
        status, execution_time, result_count, error_message
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
        where_clauses.append("(question LIKE ? OR sql LIKE ?)")
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
        ORDER BY query_id DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    records = execute_query(records_sql, tuple(params))

    items = []
    for row in records:
        items.append({
            "query_id": row["query_id"],
            "username": row["username"],
            "question": row["question"],
            "sql": row["sql"],
            "status": row["status"],
            "execution_time": row["execution_time"],
            "result_count": row["result_count"],
            "created_at": str(row["created_at"])[:19] if row.get("created_at") else "",
            "error_message": row.get("error_message", "")
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/stats")
async def get_query_stats(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取查询统计"""
    # 总查询次数
    total_result = execute_query("SELECT COUNT(*) as count FROM ai_query_logs")
    total = total_result[0]["count"] if total_result else 0

    # 成功次数
    success_result = execute_query("SELECT COUNT(*) as count FROM ai_query_logs WHERE status = 'success'")
    success = success_result[0]["count"] if success_result else 0

    # 失败次数
    failed = total - success

    # 成功率
    rate = round(success * 100 / total, 1) if total > 0 else 0

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "rate": rate
    }


@router.get("/trend")
async def get_query_trend(
    days: int = Query(default=7, ge=1, le=30),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取查询趋势"""
    result = execute_query("""
        SELECT DATE(created_at) as date, COUNT(*) as count,
               SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count
        FROM ai_query_logs
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL ? DAY)
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
async def execute_query(
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
                       0, 0, sensitive_msg)
        raise HTTPException(status_code=400, detail=sensitive_msg)

    start_time = time.time()

    try:
        # 生成 SQL
        sql, explanation = generate_sql_from_question(request.question)

        # 再次检查生成的 SQL
        sensitive_msg = check_sensitive_content(request.question, sql)
        if sensitive_msg:
            save_query_log(user_id, username, request.question, sql, "error",
                           0, 0, sensitive_msg)
            raise HTTPException(status_code=400, detail=sensitive_msg)

        # 执行查询
        data, columns = execute_sql_query(sql, request.top_k)

        execution_time = int((time.time() - start_time) * 1000)

        # 保存成功日志
        save_query_log(user_id, username, request.question, sql, "success",
                       execution_time, len(data), "")

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
                       execution_time, 0, str(e))
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
