"""
系统日志 API
提供系统日志查询、分析、导出等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from api.database import execute_query, execute_update, get_db_connection
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/logs", tags=["系统日志"])

security = HTTPBearer()


# ===========================================
# 响应模型
# ===========================================

class LogEntryResponse(BaseModel):
    """日志条目响应"""
    log_id: int
    log_level: str
    module: Optional[str]
    action: Optional[str]
    username: Optional[str]
    message: str
    ip_address: Optional[str]
    created_at: str


class LogListResponse(BaseModel):
    """日志列表响应"""
    items: List[LogEntryResponse]
    total: int
    page: int
    page_size: int


class LogStatisticsResponse(BaseModel):
    """日志统计响应"""
    total_count: int
    by_level: Dict[str, int]
    by_module: Dict[str, int]
    recent_errors: List[Dict[str, Any]]


# ===========================================
# 辅助函数
# ===========================================

def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证管理员权限"""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("sub"), "payload": payload}
    except HTTPException:
        raise HTTPException(status_code=401, detail="未授权或 token 已过期")


# ===========================================
# API 接口
# ===========================================

@router.get("", response_model=LogListResponse)
async def get_system_logs(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    level: Optional[str] = Query(None, description="日志级别：DEBUG/INFO/WARNING/ERROR"),
    module: Optional[str] = Query(None, description="模块筛选"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取系统日志列表"""
    offset = (page - 1) * page_size

    # 构建查询条件
    where_clauses = []
    params = []

    if level:
        where_clauses.append("log_level = ?")
        params.append(level)

    if module:
        where_clauses.append("module = ?")
        params.append(module)

    if keyword:
        where_clauses.append("(message LIKE ? OR username LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if start_date:
        where_clauses.append("DATE(created_at) >= ?")
        params.append(start_date)

    if end_date:
        where_clauses.append("DATE(created_at) <= ?")
        params.append(end_date)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # 查询总数
    count_sql = f"SELECT COUNT(*) as total FROM system_logs WHERE {where_sql}"
    count_result = execute_query(count_sql, tuple(params))
    total = count_result[0]["total"] if count_result else 0

    # 查询日志列表
    logs_sql = f"""
        SELECT * FROM system_logs
        WHERE {where_sql}
        ORDER BY log_id DESC
        LIMIT ? OFFSET ?
    """
    params_with_limit = list(params) + [page_size, offset]
    logs = execute_query(logs_sql, tuple(params_with_limit))

    items = []
    for log in logs:
        items.append(LogEntryResponse(
            log_id=log["log_id"],
            log_level=log["log_level"],
            module=log.get("module"),
            action=log.get("action"),
            username=log.get("username"),
            message=log.get("message", ""),
            ip_address=log.get("ip_address"),
            created_at=str(log["created_at"])[:19] if log.get("created_at") else ""
        ))

    return LogListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/stats", response_model=LogStatisticsResponse)
async def get_log_statistics(
    hours: int = Query(default=24, ge=1, le=168, description="统计时长（小时）"),
    current_user: dict = Depends(get_current_admin_user)
):
    """获取日志统计信息"""
    since = datetime.now() - timedelta(hours=hours)

    # 总数统计
    total_sql = "SELECT COUNT(*) as total FROM system_logs WHERE created_at >= ?"
    total_result = execute_query(total_sql, (since,))
    total_count = total_result[0]["total"] if total_result else 0

    # 按级别统计
    level_sql = """
        SELECT log_level, COUNT(*) as count
        FROM system_logs
        WHERE created_at >= ?
        GROUP BY log_level
    """
    level_results = execute_query(level_sql, (since,))
    by_level = {r["log_level"]: r["count"] for r in level_results} if level_results else {}

    # 按模块统计
    module_sql = """
        SELECT module, COUNT(*) as count
        FROM system_logs
        WHERE created_at >= ? AND module IS NOT NULL
        GROUP BY module
        ORDER BY count DESC
        LIMIT 10
    """
    module_results = execute_query(module_sql, (since,))
    by_module = {r["module"]: r["count"] for r in module_results} if module_results else {}

    # 最近错误日志
    error_sql = """
        SELECT log_level, module, message, created_at
        FROM system_logs
        WHERE log_level = 'ERROR' AND created_at >= ?
        ORDER BY created_at DESC
        LIMIT 10
    """
    error_results = execute_query(error_sql, (since,))
    recent_errors = []
    for err in error_results:
        recent_errors.append({
            "level": err["log_level"],
            "module": err.get("module"),
            "message": err.get("message", ""),
            "time": str(err["created_at"])[:19] if err.get("created_at") else ""
        })

    return LogStatisticsResponse(
        total_count=total_count,
        by_level=by_level,
        by_module=by_module,
        recent_errors=recent_errors
    )


@router.get("/levels")
async def get_log_levels(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取日志级别选项"""
    return [
        {"value": "DEBUG", "label": "调试"},
        {"value": "INFO", "label": "信息"},
        {"value": "WARNING", "label": "警告"},
        {"value": "ERROR", "label": "错误"}
    ]


@router.get("/modules")
async def get_log_modules(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取日志模块选项"""
    modules = execute_query("SELECT DISTINCT module FROM system_logs WHERE module IS NOT NULL")
    return [{"value": m["module"], "label": m["module"]} for m in modules] if modules else []


@router.post("")
async def create_log(
    log_level: str = "INFO",
    module: Optional[str] = None,
    action: Optional[str] = None,
    message: str = "",
    current_user: dict = Depends(get_current_admin_user)
):
    """创建系统日志（用于测试）"""
    insert_sql = """
        INSERT INTO system_logs (log_level, module, action, username, message)
        VALUES (?, ?, ?, ?, ?)
    """

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(insert_sql, (
            log_level,
            module,
            action,
            current_user.get("user_id"),
            message
        ))
        conn.commit()
        log_id = cursor.lastrowid

    return {"message": "日志创建成功", "log_id": log_id}
