"""
地产行业 ERP 报表 API
提供项目、房源、客户、销售、财务等数据统计接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from api.database import execute_query, get_db_connection
from api.auth import get_current_user

router = APIRouter(prefix="/api/realestate", tags=["地产 ERP 报表"])

security = HTTPBearer()


# ============================================
# 项目统计接口
# ============================================

@router.get("/projects/summary", response_model=dict)
async def get_projects_summary(current_user: dict = Depends(get_current_user)):
    """获取项目汇总统计"""
    sql = """
        SELECT 
            COUNT(*) as total_projects,
            COUNT(DISTINCT city) as total_cities,
            SUM(total_area) as total_area,
            SUM(total_units) as total_units,
            SUM(total_investment) as total_investment
        FROM re_projects
    """
    result = execute_query(sql)[0]
    return dict(result)


@router.get("/projects/list", response_model=dict)
async def get_projects_list(
    city: Optional[str] = None,
    project_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """获取项目列表"""
    where_clauses = []
    params = []
    
    if city:
        where_clauses.append("city = ?")
        params.append(city)
    if project_type:
        where_clauses.append("project_type = ?")
        params.append(project_type)
    if status:
        where_clauses.append("project_status = ?")
        params.append(status)
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    sql = f"""
        SELECT * FROM re_projects
        WHERE {where_sql}
        ORDER BY created_at DESC
    """
    projects = execute_query(sql, tuple(params))
    return {"items": projects, "total": len(projects)}


# ============================================
# 房源统计接口
# ============================================

@router.get("/units/summary", response_model=dict)
async def get_units_summary(current_user: dict = Depends(get_current_user)):
    """获取房源汇总统计"""
    sql = """
        SELECT 
            COUNT(*) as total_units,
            SUM(CASE WHEN unit_status = 'available' THEN 1 ELSE 0 END) as available_units,
            SUM(CASE WHEN unit_status = 'reserved' THEN 1 ELSE 0 END) as reserved_units,
            SUM(CASE WHEN unit_status = 'signed' THEN 1 ELSE 0 END) as signed_units,
            SUM(CASE WHEN unit_status = 'delivered' THEN 1 ELSE 0 END) as delivered_units,
            SUM(total_price) as total_value,
            AVG(unit_price) as avg_unit_price
        FROM re_units
    """
    result = execute_query(sql)[0]
    return dict(result)


@router.get("/units/sell-through", response_model=dict)
async def get_sell_through_rate(current_user: dict = Depends(get_current_user)):
    """获取去化率统计（按项目）"""
    sql = """
        SELECT 
            p.project_name,
            p.city,
            COUNT(u.unit_id) as total_units,
            SUM(CASE WHEN u.unit_status = 'signed' OR u.unit_status = 'delivered' THEN 1 ELSE 0 END) as sold_units,
            ROUND(
                SUM(CASE WHEN u.unit_status = 'signed' OR u.unit_status = 'delivered' THEN 1 ELSE 0 END) * 100.0 / 
                NULLIF(COUNT(u.unit_id), 0), 2
            ) as sell_through_rate
        FROM re_projects p
        LEFT JOIN re_buildings b ON p.project_id = b.project_id
        LEFT JOIN re_units u ON b.building_id = u.building_id
        GROUP BY p.project_id, p.project_name, p.city
        ORDER BY sell_through_rate DESC
    """
    stats = execute_query(sql)
    return {"items": stats}


# ============================================
# 客户统计接口
# ============================================

@router.get("/customers/summary", response_model=dict)
async def get_customers_summary(current_user: dict = Depends(get_current_user)):
    """获取客户汇总统计"""
    sql = """
        SELECT 
            COUNT(*) as total_customers,
            COUNT(DISTINCT CASE WHEN customer_type = 'personal' THEN customer_id END) as personal_customers,
            COUNT(DISTINCT CASE WHEN customer_type = 'company' THEN customer_id END) as company_customers,
            source,
            COUNT(*) as source_count
        FROM re_customers
        GROUP BY source
    """
    total = execute_query("SELECT COUNT(*) as total FROM re_customers")[0]
    by_source = execute_query(sql)
    return {
        "total": dict(total),
        "by_source": by_source
    }


# ============================================
# 销售统计接口
# ============================================

@router.get("/sales/daily", response_model=dict)
async def get_daily_sales(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """获取销售日报"""
    where_clauses = ["c.contract_status != 'cancelled'"]
    params = []
    
    if start_date:
        where_clauses.append("DATE(c.contract_date) >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("DATE(c.contract_date) <= ?")
        params.append(end_date)
    
    where_sql = " AND ".join(where_clauses)
    
    sql = f"""
        SELECT 
            DATE(c.contract_date) as report_date,
            p.project_name,
            p.city,
            COUNT(DISTINCT c.contract_id) as contract_count,
            COUNT(DISTINCT c.customer_id) as customer_count,
            SUM(c.total_price) as total_sales,
            SUM(c.area) as total_area,
            ROUND(AVG(c.unit_price), 2) as avg_unit_price,
            COALESCE(SUM(pay.total_paid), 0) as total_received
        FROM re_contracts c
        LEFT JOIN re_units u ON c.unit_id = u.unit_id
        LEFT JOIN re_buildings b ON u.building_id = b.building_id
        LEFT JOIN re_projects p ON b.project_id = p.project_id
        LEFT JOIN (
            SELECT contract_id, SUM(amount) as total_paid 
            FROM re_payments 
            GROUP BY contract_id
        ) pay ON c.contract_id = pay.contract_id
        WHERE {where_sql}
        GROUP BY DATE(c.contract_date), p.project_id, p.project_name, p.city
        ORDER BY report_date DESC
    """
    sales = execute_query(sql, tuple(params))
    return {"items": sales}


@router.get("/sales/project-performance", response_model=dict)
async def get_project_sales_performance(current_user: dict = Depends(get_current_user)):
    """获取项目销售业绩统计"""
    sql = """
        SELECT 
            p.project_name,
            p.city,
            COUNT(DISTINCT u.unit_id) as total_units,
            COUNT(DISTINCT c.contract_id) as sold_count,
            COALESCE(SUM(c.total_price), 0) as total_sales,
            ROUND(
                COUNT(DISTINCT c.contract_id) * 100.0 / NULLIF(COUNT(DISTINCT u.unit_id), 0), 2
            ) as sell_through_rate
        FROM re_projects p
        LEFT JOIN re_buildings b ON p.project_id = b.project_id
        LEFT JOIN re_units u ON b.building_id = u.building_id
        LEFT JOIN re_contracts c ON u.unit_id = c.unit_id AND c.contract_status != 'cancelled'
        GROUP BY p.project_id, p.project_name, p.city
        ORDER BY total_sales DESC
    """
    stats = execute_query(sql)
    return {"items": stats}


# ============================================
# 财务统计接口
# ============================================

@router.get("/finance/collection", response_model=dict)
async def get_collection_statistics(current_user: dict = Depends(get_current_user)):
    """获取回款统计"""
    sql = """
        SELECT 
            p.project_name,
            COUNT(DISTINCT r.receivable_id) as total_receivables,
            SUM(r.amount) as total_amount,
            SUM(r.received_amount) as total_received,
            SUM(r.balance) as total_balance,
            ROUND(
                SUM(r.received_amount) * 100.0 / NULLIF(SUM(r.amount), 0), 2
            ) as collection_rate,
            SUM(CASE WHEN r.status = 'overdue' THEN r.balance ELSE 0 END) as overdue_amount
        FROM re_receivables r
        LEFT JOIN re_contracts c ON r.contract_id = c.contract_id
        LEFT JOIN re_units u ON c.unit_id = u.unit_id
        LEFT JOIN re_buildings b ON u.building_id = b.building_id
        LEFT JOIN re_projects p ON b.project_id = p.project_id
        GROUP BY p.project_id, p.project_name
    """
    stats = execute_query(sql)
    return {"items": stats}


@router.get("/finance/payment-summary", response_model=dict)
async def get_payment_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """获取收款汇总"""
    where_clauses = []
    params = []
    
    if start_date:
        where_clauses.append("DATE(payment_date) >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("DATE(payment_date) <= ?")
        params.append(end_date)
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    sql = f"""
        SELECT 
            payment_type,
            COUNT(*) as payment_count,
            SUM(amount) as total_amount,
            payment_method,
            DATE(payment_date) as payment_date
        FROM re_payments
        WHERE {where_sql}
        GROUP BY payment_type, payment_method, DATE(payment_date)
        ORDER BY payment_date DESC
    """
    payments = execute_query(sql, tuple(params))
    return {"items": payments}


# ============================================
# 仪表盘综合数据接口
# ============================================

@router.get("/dashboard/overview", response_model=dict)
async def get_dashboard_overview(current_user: dict = Depends(get_current_user)):
    """获取仪表盘概览数据"""
    # 核心 KPI
    kpi_sql = """
        SELECT 
            (SELECT COUNT(*) FROM re_projects) as total_projects,
            (SELECT COUNT(*) FROM re_units) as total_units,
            (SELECT COUNT(*) FROM re_contracts WHERE contract_status != 'cancelled') as total_contracts,
            (SELECT SUM(total_price) FROM re_contracts WHERE contract_status != 'cancelled') as total_sales,
            (SELECT SUM(amount) FROM re_payments) as total_received,
            (SELECT SUM(balance) FROM re_receivables) as total_receivables
    """
    kpi = execute_query(kpi_sql)[0]
    
    # 最近销售
    recent_sales_sql = """
        SELECT 
            c.contract_code,
            c.total_price,
            c.contract_date,
            cu.customer_name,
            p.project_name,
            u.unit_name
        FROM re_contracts c
        LEFT JOIN re_customers cu ON c.customer_id = cu.customer_id
        LEFT JOIN re_units u ON c.unit_id = u.unit_id
        LEFT JOIN re_buildings b ON u.building_id = b.building_id
        LEFT JOIN re_projects p ON b.project_id = p.project_id
        ORDER BY c.contract_date DESC
        LIMIT 10
    """
    recent_sales = execute_query(recent_sales_sql)
    
    # 去化率排名
    sell_through_sql = """
        SELECT 
            p.project_name,
            ROUND(
                COUNT(DISTINCT CASE WHEN u.unit_status IN ('signed', 'delivered') THEN u.unit_id END) * 100.0 / 
                NULLIF(COUNT(DISTINCT u.unit_id), 0), 2
            ) as sell_through_rate
        FROM re_projects p
        LEFT JOIN re_buildings b ON p.project_id = b.project_id
        LEFT JOIN re_units u ON b.building_id = u.building_id
        GROUP BY p.project_id, p.project_name
        ORDER BY sell_through_rate DESC
        LIMIT 5
    """
    sell_through_ranking = execute_query(sell_through_sql)
    
    return {
        "kpi": dict(kpi),
        "recent_sales": recent_sales,
        "sell_through_ranking": sell_through_ranking
    }
