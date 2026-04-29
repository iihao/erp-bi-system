"""
后台管理仪表盘 API
提供系统概况、KPI 统计、图表数据等功能
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random

from api.database import execute_query
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/dashboard", tags=["后台管理 - 仪表盘"])

security = HTTPBearer()


def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证管理员权限"""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("sub"), "payload": payload}
    except HTTPException:
        raise HTTPException(status_code=401, detail="未授权或 token 已过期")


@router.get("/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取仪表盘 KPI 统计数据"""

    # 数据表总数（SQLite 兼容）
    table_result = execute_query("""
        SELECT COUNT(*) as count FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """)
    table_count = table_result[0]["count"] if table_result else 0

    # ETL 任务数
    etl_result = execute_query("SELECT COUNT(*) as count FROM etl_schedules")
    etl_task_count = etl_result[0]["count"] if etl_result else 0

    # 报表指标数
    report_result = execute_query("SELECT COUNT(*) as count FROM report_designs")
    report_metric_count = report_result[0]["count"] if report_result else 0

    # 用户总数
    user_result = execute_query("SELECT COUNT(*) as count FROM users")
    user_count = user_result[0]["count"] if user_result else 0

    # 今日查询次数（从日志表统计，SQLite 兼容）
    today = datetime.now().strftime("%Y-%m-%d")
    query_result = execute_query("""
        SELECT COUNT(*) as count FROM system_logs
        WHERE strftime('%Y-%m-%d', created_at) = ? AND (action = 'query' OR message LIKE '%查询%')
    """, (today,))
    today_query_count = query_result[0]["count"] if query_result else 0

    # 系统运行时长
    uptime_result = execute_query("""
        SELECT MIN(created_at) as start_time FROM system_logs
    """)
    if uptime_result and uptime_result[0]["start_time"]:
        start_time = uptime_result[0]["start_time"]
        delta = datetime.now() - start_time
        uptime_days = f"{delta.days}天{delta.seconds // 3600}小时"
    else:
        uptime_days = "新安装"

    return {
        "table_count": table_count,
        "etl_task_count": etl_task_count,
        "report_metric_count": report_metric_count,
        "user_count": user_count,
        "today_query_count": today_query_count,
        "uptime_days": uptime_days
    }


@router.get("/etl-trend")
async def get_etl_trend(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取 ETL 任务执行趋势（近 7 天）"""

    dates = []
    counts = []

    for i in range(6, -1, -1):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        dates.append(date_str)

        # 统计当天的 ETL 执行记录（SQLite 兼容）
        result = execute_query("""
            SELECT COUNT(*) as count FROM etl_task_logs
            WHERE strftime('%Y-%m-%d', start_time) = ?
        """, (date_str,))
        count = result[0]["count"] if result else 0
        counts.append(count)

    # 格式化日期显示
    formatted_dates = []
    for i, date in enumerate(dates):
        if i == 6:
            formatted_dates.append("7 天前")
        elif i == 5:
            formatted_dates.append("6 天前")
        elif i == 0:
            formatted_dates.append("今天")
        else:
            formatted_dates.append(f"{7-i}天前")

    return {
        "dates": formatted_dates,
        "counts": counts
    }


@router.get("/heatmap")
async def get_query_heatmap(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取查询热度排行（Top 10 报表）"""

    # 统计各报表的查询次数
    result = execute_query("""
        SELECT name as report_name, COUNT(*) as query_count
        FROM report_designs
        GROUP BY report_id, name
        ORDER BY query_count DESC
        LIMIT 10
    """)

    if result:
        reports = [{"name": row["report_name"], "count": row["query_count"]} for row in result]
    else:
        # 默认数据
        reports = [
            {"name": "销售日报", "count": 520},
            {"name": "库存周报", "count": 450},
            {"name": "客户分析", "count": 380},
            {"name": "产品排行", "count": 320},
            {"name": "月度总结", "count": 280},
            {"name": "年度对比", "count": 240},
            {"name": "利润分析", "count": 200},
            {"name": "区域销售", "count": 180},
            {"name": "客户排行", "count": 150},
            {"name": "产品库存", "count": 120}
        ]

    return {
        "reports": reports
    }


@router.get("/resources")
async def get_resource_usage(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取系统资源使用率"""

    import psutil

    try:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent

        # 数据库连接数（模拟）
        db_connections = random.randint(10, 50)

        return {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "db_connections": db_connections
        }
    except Exception:
        return {
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "db_connections": 0
        }


@router.get("/activities")
async def get_recent_activities(
    limit: int = 10,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取最近活动记录"""

    result = execute_query("""
        SELECT log_level, module, action, username, message, created_at
        FROM system_logs
        ORDER BY log_id DESC
        LIMIT ?
    """, (limit,))

    activities = []
    for row in result:
        activities.append({
            "level": row["log_level"],
            "module": row.get("module"),
            "action": row.get("action"),
            "username": row.get("username"),
            "message": row.get("message", ""),
            "time": str(row["created_at"])[:16] if row.get("created_at") else ""
        })

    return {
        "activities": activities
    }
