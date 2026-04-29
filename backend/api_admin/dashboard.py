"""
后台管理仪表板 API
提供概览数据、统计指标、快捷入口等功能
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from api.database import execute_query
from api.auth import decode_token

router = APIRouter(prefix="/api/admin/dashboard", tags=["后台管理 - 仪表板"])

security = HTTPBearer()


# ===========================================
# 响应模型
# ===========================================

class DashboardStatsResponse(BaseModel):
    """仪表板统计响应"""
    total_users: int
    active_users: int
    total_roles: int
    total_reports: int
    published_reports: int
    total_etl_jobs: int
    successful_jobs: int
    total_etl_runs: int
    recent_ai_queries: int


class RecentActivityResponse(BaseModel):
    """最近活动响应"""
    activity_id: int
    activity_type: str
    description: str
    username: Optional[str]
    created_at: str


class QuickStatsResponse(BaseModel):
    """快捷统计响应"""
    label: str
    value: int
    trend: Optional[float]
    unit: str


class RealEstateStatsResponse(BaseModel):
    """地产经营统计响应"""
    total_projects: int
    total_units: int
    total_subscriptions: int
    total_contracts: int
    total_sales: float
    total_received: float
    total_receivables: float
    total_cost: float
    total_expense: float
    total_profit: float
    subscription_rate: float
    collection_rate: float
    cost_ratio: float
    expense_ratio: float
    profit_margin: float


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

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取仪表板统计数据"""
    # 用户统计
    total_users_result = execute_query("SELECT COUNT(*) as total FROM users")
    total_users = total_users_result[0]["total"] if total_users_result else 0

    active_users_result = execute_query("SELECT COUNT(*) as total FROM users WHERE status = 1")
    active_users = active_users_result[0]["total"] if active_users_result else 0

    # 角色统计
    total_roles_result = execute_query("SELECT COUNT(*) as total FROM roles")
    total_roles = total_roles_result[0]["total"] if total_roles_result else 0

    # 报表统计
    total_reports_result = execute_query("SELECT COUNT(*) as total FROM report_configs")
    total_reports = total_reports_result[0]["total"] if total_reports_result else 0

    published_reports_result = execute_query("SELECT COUNT(*) as total FROM report_configs WHERE status = 'published'")
    published_reports = published_reports_result[0]["total"] if published_reports_result else 0

    # ETL 作业统计
    total_jobs_result = execute_query("SELECT COUNT(*) as total FROM etl_jobs")
    total_etl_jobs = total_jobs_result[0]["total"] if total_jobs_result else 0

    successful_jobs_result = execute_query("SELECT COUNT(*) as total FROM etl_jobs WHERE status = 'active'")
    successful_jobs = successful_jobs_result[0]["total"] if successful_jobs_result else 0

    # ETL 运行统计
    total_runs_result = execute_query("SELECT COUNT(*) as total FROM etl_task_logs")
    total_etl_runs = total_runs_result[0]["total"] if total_runs_result else 0

    # AI 查询统计（最近 7 天）
    seven_days_ago = datetime.now() - timedelta(days=7)
    ai_queries_result = execute_query(
        "SELECT COUNT(*) as total FROM ai_query_logs WHERE created_at >= ?",
        (seven_days_ago,)
    )
    recent_ai_queries = ai_queries_result[0]["total"] if ai_queries_result else 0

    return DashboardStatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_roles=total_roles,
        total_reports=total_reports,
        published_reports=published_reports,
        total_etl_jobs=total_etl_jobs,
        successful_jobs=successful_jobs,
        total_etl_runs=total_etl_runs,
        recent_ai_queries=recent_ai_queries
    )


@router.get("/quick-stats", response_model=List[QuickStatsResponse])
async def get_quick_stats(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取快捷统计数据"""
    stats = []

    # 用户总数
    result = execute_query("SELECT COUNT(*) as total FROM users")
    stats.append(QuickStatsResponse(
        label="用户总数",
        value=result[0]["total"] if result else 0,
        trend=None,
        unit="人"
    ))

    # 报表总数
    result = execute_query("SELECT COUNT(*) as total FROM report_configs")
    stats.append(QuickStatsResponse(
        label="报表总数",
        value=result[0]["total"] if result else 0,
        trend=None,
        unit="个"
    ))

    # ETL 作业数
    result = execute_query("SELECT COUNT(*) as total FROM etl_jobs")
    stats.append(QuickStatsResponse(
        label="ETL 作业",
        value=result[0]["total"] if result else 0,
        trend=None,
        unit="个"
    ))

    # AI 查询数（最近 7 天）
    seven_days_ago = datetime.now() - timedelta(days=7)
    result = execute_query(
        "SELECT COUNT(*) as total FROM ai_query_logs WHERE created_at >= ?",
        (seven_days_ago,)
    )
    stats.append(QuickStatsResponse(
        label="AI 查询 (7 天)",
        value=result[0]["total"] if result else 0,
        trend=None,
        unit="次"
    ))

    return stats


@router.get("/real-estate-stats", response_model=RealEstateStatsResponse)
async def get_real_estate_stats(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取地产经营统计数据"""
    def _safe_number(value):
        return float(value or 0)

    total_projects_result = execute_query("SELECT COUNT(*) as total FROM re_projects")
    total_units_result = execute_query("SELECT COUNT(*) as total FROM re_units")
    total_subscriptions_result = execute_query("SELECT COUNT(*) as total FROM re_subscriptions")
    total_contracts_result = execute_query("SELECT COUNT(*) as total FROM re_contracts WHERE contract_status != 'cancelled'")

    total_projects = total_projects_result[0]["total"] if total_projects_result else 0
    total_units = total_units_result[0]["total"] if total_units_result else 0
    total_subscriptions = total_subscriptions_result[0]["total"] if total_subscriptions_result else 0
    total_contracts = total_contracts_result[0]["total"] if total_contracts_result else 0

    total_sales_result = execute_query("SELECT COALESCE(SUM(total_price), 0) as total FROM re_contracts WHERE contract_status != 'cancelled'")
    total_sales = _safe_number(total_sales_result[0]["total"] if total_sales_result else 0)

    total_received_result = execute_query("SELECT COALESCE(SUM(amount), 0) as total FROM re_payments")
    total_received = _safe_number(total_received_result[0]["total"] if total_received_result else 0)

    total_receivables_result = execute_query("SELECT COALESCE(SUM(balance), 0) as total FROM re_receivables")
    total_receivables = _safe_number(total_receivables_result[0]["total"] if total_receivables_result else 0)

    total_cost_result = execute_query("SELECT COALESCE(SUM(actual_amount), 0) as total FROM ads_project_cost_report")
    total_cost = _safe_number(total_cost_result[0]["total"] if total_cost_result else 0)

    total_expense_result = execute_query("SELECT COALESCE(SUM(total_cost), 0) as total FROM ads_finance_dashboard")
    total_expense = _safe_number(total_expense_result[0]["total"] if total_expense_result else 0)
    if total_expense == 0:
        fallback_expense = execute_query("SELECT COALESCE(SUM(fee_amount), 0) as total FROM dws_sales_cost_fact")
        total_expense = _safe_number(fallback_expense[0]["total"] if fallback_expense else 0)

    total_profit_result = execute_query("SELECT COALESCE(SUM(total_profit), 0) as total FROM ads_finance_dashboard")
    total_profit = _safe_number(total_profit_result[0]["total"] if total_profit_result else 0)
    if total_profit == 0 and total_sales:
        total_profit = total_sales - total_cost - total_expense

    subscription_rate = round(total_contracts * 100.0 / total_subscriptions, 2) if total_subscriptions else 0
    collection_rate = round(total_received * 100.0 / total_sales, 2) if total_sales else 0
    cost_ratio = round(total_cost * 100.0 / total_sales, 2) if total_sales else 0
    expense_ratio = round(total_expense * 100.0 / total_sales, 2) if total_sales else 0
    profit_margin = round(total_profit * 100.0 / total_sales, 2) if total_sales else 0

    return RealEstateStatsResponse(
        total_projects=int(total_projects),
        total_units=int(total_units),
        total_subscriptions=int(total_subscriptions),
        total_contracts=int(total_contracts),
        total_sales=total_sales,
        total_received=total_received,
        total_receivables=total_receivables,
        total_cost=total_cost,
        total_expense=total_expense,
        total_profit=total_profit,
        subscription_rate=subscription_rate,
        collection_rate=collection_rate,
        cost_ratio=cost_ratio,
        expense_ratio=expense_ratio,
        profit_margin=profit_margin
    )


@router.get("/recent-activities", response_model=List[RecentActivityResponse])
async def get_recent_activities(
    limit: int = 10,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取最近活动记录"""
    # 从系统日志中获取最近活动
    logs = execute_query("""
        SELECT log_id, 'log' as activity_type,
               COALESCE(action, module, 'system') as description,
               username, created_at
        FROM system_logs
        ORDER BY log_id DESC
        LIMIT ?
    """, (limit,))

    activities = []
    for log in logs:
        activities.append(RecentActivityResponse(
            activity_id=log["log_id"],
            activity_type=log["activity_type"],
            description=log["description"],
            username=log.get("username"),
            created_at=str(log["created_at"])[:19] if log.get("created_at") else ""
        ))

    return activities


@router.get("/chart-data/users-trend")
async def get_users_trend(
    days: int = 7,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取用户增长趋势"""
    trend_data = []
    now = datetime.now()

    for i in range(days - 1, -1, -1):
        date = now - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        next_date = date + timedelta(days=1)

        result = execute_query("""
            SELECT COUNT(*) as total FROM users
            WHERE created_at >= ? AND created_at < ?
        """, (date_str, next_date))

        trend_data.append({
            "date": date_str,
            "count": result[0]["total"] if result else 0
        })

    return {"days": days, "data": trend_data}


@router.get("/chart-data/etl-status")
async def get_etl_status_chart(
    current_user: dict = Depends(get_current_admin_user)
):
    """获取 ETL 任务状态分布"""
    result = execute_query("""
        SELECT status, COUNT(*) as count
        FROM etl_task_logs
        WHERE created_at >= DATE('now', '-7 days')
        GROUP BY status
    """)

    return {
        "labels": [r["status"] for r in result] if result else [],
        "values": [r["count"] for r in result] if result else []
    }
